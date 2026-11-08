from __future__ import annotations

import importlib.util
import re
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "username_analysis.py"
SPEC = importlib.util.spec_from_file_location("username_analysis", MODULE_PATH)
assert SPEC and SPEC.loader
username_analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(username_analysis)


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
                job_timeout=60,
                site=[],
                proxy=None,
                print_all=False,
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
