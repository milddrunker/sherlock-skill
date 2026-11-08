#!/usr/bin/env python3
"""Run the embedded username scanner and scaffold a public-source report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import sherlock_scan


ANSI_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
FOUND_RE = re.compile(r"^\[\+\]\s+(.+?):\s+(https?://\S+)\s*$")
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
CONCLUSIONS = {"Confirmed", "Likely", "Possible", "Unrelated", "Inconclusive"}

REQUIRED_HEADINGS = (
    "## Scope and Authorization",
    "## Evidence Standard",
    "## Candidate Accounts",
    "## Iterative Discovery",
    "## Cross-Platform Verification",
    "## Integrated Account Map",
    "## Identity Assessment",
    "## Public Profile Summary",
    "## Login-Required Information Gaps",
    "## Sources",
    "## Limitations",
)


class AnalysisError(RuntimeError):
    """A user-actionable workflow error."""


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sanitized_slug(username: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", username).strip("._-")[:64]
    if not base:
        base = "username"
    digest = hashlib.sha256(username.encode("utf-8")).hexdigest()[:8]
    if base != username or len(username) > 64:
        return f"{base}-{digest}"
    return base


def parse_findings(output: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw_line in output.splitlines():
        line = ANSI_RE.sub("", raw_line).strip()
        match = FOUND_RE.match(line)
        if not match:
            continue
        site = match.group(1).strip()
        url = match.group(2).rstrip(".,);")
        key = (site.casefold(), url)
        if key in seen:
            continue
        seen.add(key)
        findings.append(
            {
                "id": f"F{len(findings) + 1:03d}",
                "site": site,
                "url": url,
                "verification_status": "unreviewed",
                "linkage": "unassessed",
                "confidence": "unassessed",
                "notes": "",
            }
        )
    return findings


def run_embedded_scan(args: argparse.Namespace) -> tuple[dict, list[dict[str, str]]]:
    try:
        scan = sherlock_scan.scan_sites(
            args.username,
            site_names=args.site,
            timeout=args.timeout,
            workers=args.workers,
            proxy=args.proxy,
            include_nsfw=args.include_nsfw,
        )
    except sherlock_scan.ScanError as exc:
        raise AnalysisError(str(exc)) from exc

    findings = []
    for result in scan["results"]:
        if result["status"] != "claimed":
            continue
        findings.append(
            {
                "id": f"F{len(findings) + 1:03d}",
                "site": result["site"],
                "url": result["url"],
                "http_status": result["http_status"],
                "scan_reason": result["reason"],
                "verification_status": "unreviewed",
                "linkage": "unassessed",
                "confidence": "unassessed",
                "notes": "",
            }
        )
    return scan, findings


def render_scan_output(scan: dict, findings: list[dict[str, str]]) -> str:
    lines = [f"[*] Checking username {scan['username']} on:"]
    for finding in findings:
        lines.append(f"[+] {finding['site']}: {finding['url']}")
    summary = scan["summary"]
    lines.append(
        f"[*] Search completed with {len(findings)} results; "
        f"{summary['unknown']} unknown, {summary['waf']} blocked, "
        f"{summary['available']} not found."
    )
    return "\n".join(lines) + "\n"


def markdown_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def findings_table(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "| - | No candidates found | - | - | - | - |"
    rows = []
    for finding in findings:
        rows.append(
            "| {id} | {site} | <{url}> | Unreviewed | [Add public facts] | [Add S#] |".format(
                id=markdown_escape(finding["id"]),
                site=markdown_escape(finding["site"]),
                url=finding["url"],
            )
        )
    return "\n".join(rows)


def create_case(args: argparse.Namespace) -> Path:
    if not args.username.strip():
        raise AnalysisError("Username cannot be empty.")

    workspace = Path(args.workspace).expanduser().resolve()
    case_dir = workspace / "username_analysis" / sanitized_slug(args.username)
    report_path = case_dir / "username_analysis.md"

    if case_dir.exists() and any(case_dir.iterdir()) and not args.force:
        raise AnalysisError(
            f"Case directory already contains files: {case_dir}. "
            "Use `--force` only when replacing it is intentional."
        )
    case_dir.mkdir(parents=True, exist_ok=True)

    scan = None
    if args.from_output:
        output_path = Path(args.from_output).expanduser().resolve()
        try:
            stdout = output_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise AnalysisError(f"Could not read scanner output: {exc}") from exc
        findings = parse_findings(stdout)
        stderr = ""
        source_mode = "provided-output"
    else:
        scan, findings = run_embedded_scan(args)
        stdout = render_scan_output(scan, findings)
        stderr = ""
        source_mode = "embedded"

    analyzed_at = utc_now()

    (case_dir / "sherlock-output.txt").write_text(stdout, encoding="utf-8")
    (case_dir / "sherlock-error.txt").write_text(stderr, encoding="utf-8")
    if scan is not None:
        (case_dir / "sherlock-scan.json").write_text(
            json.dumps(scan, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    evidence = {
        "schema_version": 2,
        "username": args.username,
        "analyzed_at": analyzed_at,
        "source_mode": source_mode,
        "scanner": {
            "engine": "embedded-python-stdlib" if scan else "provided-output",
            "version": sherlock_scan.SCANNER_VERSION if scan else None,
            "timeout_seconds": args.timeout,
            "workers": getattr(args, "workers", None),
            "sites": args.site,
            "proxy_configured": bool(args.proxy),
            "output_file": "sherlock-output.txt",
            "full_scan_file": "sherlock-scan.json" if scan else None,
            "summary": scan["summary"] if scan else None,
        },
        "summary": {
            "candidate_count": len(findings),
            "platforms": [finding["site"] for finding in findings],
        },
        "findings": findings,
        "discovery": {
            "strategy": "bounded_public_pivots",
            "limits": {
                "default_derived_rounds": 2,
                "default_lead_checks": 12,
            },
            "rounds": [
                {
                    "round": 1,
                    "seed_type": "username",
                    "seed_value": args.username,
                    "method": "embedded-site-scan" if scan else "provided-output",
                    "status": "initialized",
                    "outcome": "Initial candidates require review before extracting leads.",
                    "sources": [],
                }
            ],
            "candidates": [],
            "leads": [],
            "clusters": [],
        },
        "identity_assessment": {
            "conclusion": "Inconclusive",
            "confidence": "Low",
            "summary": "",
        },
    }
    (case_dir / "evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    template_path = Path(__file__).resolve().parent.parent / "assets" / "report_template.md"
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AnalysisError(f"Could not read report template: {exc}") from exc

    report = (
        template.replace("{{USERNAME}}", markdown_escape(args.username))
        .replace("{{ANALYZED_AT}}", analyzed_at)
        .replace("{{FINDING_COUNT}}", str(len(findings)))
        .replace("{{FINDINGS_TABLE}}", findings_table(findings))
    )
    report_path.write_text(report, encoding="utf-8")

    print(f"Created case directory: {case_dir}")
    print(f"Candidate accounts: {len(findings)}")
    print(f"Report scaffold: {report_path}")
    if scan and scan["summary"]["unknown"]:
        print(
            f"Warning: {scan['summary']['unknown']} sites returned unknown "
            "results; review sherlock-scan.json before relying on coverage.",
            file=sys.stderr,
        )
    return report_path


def validate_report(report_path: Path) -> tuple[list[str], list[str]]:
    try:
        report = report_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Could not read report: {exc}"], []

    errors: list[str] = []
    warnings: list[str] = []

    placeholders = sorted(set(PLACEHOLDER_RE.findall(report)))
    if placeholders:
        errors.append("Unresolved placeholders: " + ", ".join(placeholders))
    if re.search(r"\bTODO\b|\[TODO", report, flags=re.IGNORECASE):
        errors.append("The report still contains a TODO marker.")

    for heading in REQUIRED_HEADINGS:
        if heading not in report:
            errors.append(f"Missing required heading: {heading}")

    conclusion_match = re.search(
        r"-\s+\*\*Conclusion:\*\*\s+([A-Za-z]+)", report
    )
    if not conclusion_match:
        errors.append("Identity conclusion is missing.")
    elif conclusion_match.group(1) not in CONCLUSIONS:
        errors.append(
            "Identity conclusion must be one of: " + ", ".join(sorted(CONCLUSIONS))
        )

    if not re.search(r"-\s+\*\*Confidence:\*\*\s+(High|Medium|Low)", report):
        errors.append("Identity confidence must be High, Medium, or Low.")
    if "| Unreviewed |" in report:
        errors.append("At least one candidate row is still marked Unreviewed.")
    if re.search(
        r"\[(?:Add|State|List|Explain|Reference|Summarize|Concrete|Account A|"
        r"Specific overlap|Strong /|Linkage or|Reasoning|Unknown or|"
        r"YYYY-MM-DD|Claim|Primary platform|High /)",
        report,
    ):
        errors.append("Bracketed report guidance still needs replacement.")

    source_section = report.split("## Sources", 1)
    if len(source_section) == 2:
        sources = source_section[1].split("##", 1)[0]
        count_match = re.search(r"Sherlock reported \*\*(\d+)\*\*", report)
        candidate_count = int(count_match.group(1)) if count_match else 0
        if candidate_count > 0 and not re.search(r"https?://", sources):
            errors.append("Candidate accounts exist, but Sources has no public URL.")
        if candidate_count > 0 and not re.search(r"\|\s*S\d+\s*\|", sources):
            errors.append("Candidate accounts exist, but Sources has no source ID.")
    else:
        errors.append("Sources section could not be parsed.")

    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the embedded scanner and scaffold a public-source report."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Create a new username analysis case.")
    collect.add_argument("--username", required=True, help="Username or approved alias.")
    collect.add_argument(
        "--workspace",
        default=".",
        help="Workspace root; output goes under username_analysis/ (default: current directory).",
    )
    collect.add_argument(
        "--from-output",
        help="Parse an existing compatible scanner capture instead of scanning.",
    )
    collect.add_argument(
        "--timeout", type=float, default=10, help="Per-site timeout in seconds."
    )
    collect.add_argument(
        "--workers", type=int, default=20, help="Concurrent requests (default: 20)."
    )
    collect.add_argument("--site", action="append", default=[], help="Limit to a site; repeatable.")
    collect.add_argument("--proxy", help="HTTP or HTTPS proxy URL.")
    collect.add_argument(
        "--include-nsfw", action="store_true", help="Include NSFW site definitions."
    )
    collect.add_argument("--force", action="store_true", help="Replace an existing case directory.")

    validate = subparsers.add_parser("validate", help="Validate a completed report.")
    validate.add_argument("report", type=Path)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "collect":
            create_case(args)
            return 0

        report_path = args.report.expanduser().resolve()
        errors, warnings = validate_report(report_path)
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        for message in warnings:
            print(f"WARNING: {message}", file=sys.stderr)
        if errors:
            return 1
        print(f"Report validation passed: {report_path}")
        return 0
    except AnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
