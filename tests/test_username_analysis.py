from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = ROOT / "scripts" / "username_analysis.py"
SPEC = importlib.util.spec_from_file_location("username_analysis", MODULE_PATH)
assert SPEC and SPEC.loader
username_analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(username_analysis)
sherlock_scan = username_analysis.sherlock_scan


class UsernameAnalysisTests(unittest.TestCase):
    def test_parse_findings_strips_ansi_and_deduplicates(self) -> None:
        output = (
            "\x1b[32m[+] GitHub: https://github.com/example\x1b[0m\n"
            "[+] GitHub: https://github.com/example\n"
            "[+] Gitee: https://gitee.com/example/\n"
            "[*] Search completed\n"
        )

        findings = username_analysis.parse_findings(output)

        self.assertEqual([item["site"] for item in findings], ["GitHub", "Gitee"])
        self.assertEqual(findings[0]["id"], "F001")
        self.assertEqual(findings[1]["id"], "F002")

    def test_slug_cannot_escape_analysis_directory(self) -> None:
        slug = username_analysis.sanitized_slug("../../Example User")

        self.assertNotIn("/", slug)
        self.assertNotIn("\\", slug)
        self.assertTrue(slug.startswith("Example_User-"))

    def test_collect_from_output_scaffolds_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            captured = root / "captured.txt"
            captured.write_text(
                "[+] Codeforces: https://codeforces.com/profile/example_user\n",
                encoding="utf-8",
            )
            args = types.SimpleNamespace(
                username="example_user",
                workspace=str(root),
                from_output=str(captured),
                force=False,
                sherlock_command=None,
                timeout=10,
                workers=20,
                site=[],
                proxy=None,
                include_nsfw=False,
            )

            report_path = username_analysis.create_case(args)
            evidence = (
                root / "username_analysis" / "example_user" / "evidence.json"
            ).read_text(encoding="utf-8")

            self.assertTrue(report_path.exists())
            self.assertIn('"candidate_count": 1', evidence)
            self.assertIn("https://codeforces.com/profile/example_user", evidence)
            self.assertIn("{{PURPOSE}}", report_path.read_text(encoding="utf-8"))

            errors, _ = username_analysis.validate_report(report_path)
            self.assertTrue(any("Unresolved placeholders" in error for error in errors))
            self.assertTrue(any("Unreviewed" in error for error in errors))

    def test_embedded_scan_scaffolds_without_external_command(self) -> None:
        scan = {
            "username": "example_user",
            "summary": {
                "sites_scanned": 1,
                "claimed": 1,
                "available": 0,
                "unknown": 0,
                "illegal": 0,
                "waf": 0,
            },
            "results": [
                {
                    "site": "GitHub",
                    "url": "https://github.com/example_user",
                    "status": "claimed",
                    "http_status": 200,
                    "reason": "HTTP 200; successful profile response.",
                    "elapsed_seconds": 0.1,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            args = types.SimpleNamespace(
                username="example_user",
                workspace=temp_dir,
                from_output=None,
                force=False,
                timeout=10,
                workers=20,
                site=["GitHub"],
                proxy=None,
                include_nsfw=False,
            )
            with mock.patch.object(
                username_analysis.sherlock_scan,
                "scan_sites",
                return_value=scan,
            ) as scan_mock:
                report_path = username_analysis.create_case(args)

            scan_mock.assert_called_once()
            case_dir = report_path.parent
            evidence = json.loads(
                (case_dir / "evidence.json").read_text(encoding="utf-8")
            )
            self.assertEqual(evidence["source_mode"], "embedded")
            self.assertEqual(evidence["summary"]["candidate_count"], 1)
            self.assertTrue((case_dir / "sherlock-scan.json").exists())

    def test_bundled_sites_are_valid(self) -> None:
        sites = sherlock_scan.load_sites()

        self.assertGreaterEqual(len(sites), 400)
        self.assertIn("GitHub", sites)
        self.assertIn("url", sites["GitHub"])

    def test_agent_manifest_is_self_contained(self) -> None:
        manifest = json.loads(
            (ROOT / "agent-manifest.json").read_text(encoding="utf-8")
        )

        self.assertEqual(manifest["name"], "sherlock-skill")
        self.assertEqual(manifest["runtime"]["dependencies"], [])
        self.assertFalse(manifest["authentication"]["required"])
        for relative_path in manifest["instructions"].values():
            self.assertTrue((ROOT / relative_path).exists())
        for entrypoint in manifest["entrypoints"].values():
            command = entrypoint["command"]
            script_path = ROOT / command[1]
            self.assertTrue(script_path.exists())

    def test_classification_message_rule(self) -> None:
        site = {
            "errorType": "message",
            "errorMsg": "This account does not exist",
        }
        missing = {
            "status_code": 200,
            "text": "This account does not exist",
            "network_error": None,
        }
        claimed = {
            "status_code": 200,
            "text": "Public profile content",
            "network_error": None,
        }

        self.assertEqual(sherlock_scan.classify_response(site, missing)[0], "available")
        self.assertEqual(sherlock_scan.classify_response(site, claimed)[0], "claimed")

    def test_classification_status_and_waf_rules(self) -> None:
        status_site = {"errorType": "status_code", "errorCode": 404}
        available = {"status_code": 404, "text": "", "network_error": None}
        claimed = {"status_code": 200, "text": "", "network_error": None}
        waf = {
            "status_code": 200,
            "text": '<span id="challenge-error-text">',
            "network_error": None,
        }

        self.assertEqual(
            sherlock_scan.classify_response(status_site, available)[0], "available"
        )
        self.assertEqual(
            sherlock_scan.classify_response(status_site, claimed)[0], "claimed"
        )
        self.assertEqual(
            sherlock_scan.classify_response(status_site, waf)[0], "waf"
        )

    def test_complete_empty_result_report_passes_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = (
                ROOT / "assets" / "report_template.md"
            ).read_text(encoding="utf-8")
            report = report.replace("{{USERNAME}}", "not_found_anywhere")
            report = report.replace("{{ANALYZED_AT}}", "2026-01-01T00:00:00Z")
            report = report.replace("{{FINDING_COUNT}}", "0")
            report = report.replace(
                "{{FINDINGS_TABLE}}",
                "| - | No candidates found | - | - | - | - |",
            )
            replacements = {
                "PURPOSE": "Authorized public-source check.",
                "AUTHORIZATION": "Requester confirmed authorization.",
                "EXECUTIVE_ASSESSMENT": "No candidate accounts were found.",
                "CROSS_PLATFORM_TABLE": "No cross-platform comparison was possible.",
                "GROUPED_ACCOUNTS": "None.",
                "DECISIVE_EVIDENCE": "None.",
                "MISSING_OR_CONTRADICTORY_EVIDENCE": "No accounts were found.",
                "OBSERVABLE_FACTS": "Sherlock returned no candidate rows.",
                "CONSISTENT_ATTRIBUTES": "None.",
                "DIFFERENCES_AND_CONTRADICTIONS": "None.",
                "REASONED_INFERENCES": "No identity inference was made.",
                "TIMELINE_ROWS": "No public activity was identified.",
                "SOURCES_TABLE": "| - | None | - | No candidates | Not applicable |",
                "CASE_LIMITATIONS": "This run covered the configured Sherlock site list.",
                "RECOMMENDATIONS": "Do not infer identity from failed checks alone.",
            }
            for key, value in replacements.items():
                report = report.replace("{{" + key + "}}", value)

            report_path = Path(temp_dir) / "username_analysis.md"
            report_path.write_text(report, encoding="utf-8")
            errors, warnings = username_analysis.validate_report(report_path)

            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            self.assertIsNone(
                re.search(r"\{\{[A-Z0-9_]+\}\}", report_path.read_text(encoding="utf-8"))
            )


if __name__ == "__main__":
    unittest.main()
