#!/usr/bin/env python3
"""Collect Sherlock results and scaffold a public-source username report."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ANSI_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
FOUND_RE = re.compile(r"^\[\+\]\s+(.+?):\s+(https?://\S+)\s*$")
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
CONCLUSIONS = {"Confirmed", "Likely", "Possible", "Unrelated", "Inconclusive"}

REQUIRED_HEADINGS = (
    "## Scope and Authorization",
    "## Evidence Standard",
    "## Candidate Accounts",
    "## Cross-Platform Verification",
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


def resolve_sherlock(explicit: str | None) -> list[str]:
    if explicit:
        resolved = shutil.which(explicit) or explicit
        if not Path(resolved).is_file():
            raise AnalysisError(f"Sherlock executable not found: {explicit}")
        return [resolved]

    executable = shutil.which("sherlock")
    if executable:
        return [executable]

    if importlib.util.find_spec("sherlock_project.sherlock") is not None:
        code = (
            "from sherlock_project.sherlock import main; "
            "raise SystemExit(main())"
        )
        return [sys.executable, "-c", code]

    raise AnalysisError(
        "Sherlock is not on PATH. Install it with "
        "`pipx install sherlock-project`, pass `--sherlock-command`, "
        "or use `--from-output` with an existing capture."
    )


def run_sherlock(args: argparse.Namespace) -> tuple[str, str, int, list[str]]:
    command = resolve_sherlock(args.sherlock_command)
    invocation = command + [args.username, "--no-color", "--timeout", str(args.timeout)]
    invocation.extend(["--local"])
    if args.print_all:
        invocation.append("--print-all")
    else:
        invocation.append("--print-found")
    if args.proxy:
        invocation.extend(["--proxy", args.proxy])
    for site in args.site:
        invocation.extend(["--site", site])

    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        completed = subprocess.run(
            invocation,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=args.job_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AnalysisError(
            f"Sherlock exceeded the overall timeout ({args.job_timeout}s)."
        ) from exc
    except OSError as exc:
        raise AnalysisError(f"Could not start Sherlock: {exc}") from exc

    return completed.stdout, completed.stderr, completed.returncode, invocation


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

    if args.from_output:
        output_path = Path(args.from_output).expanduser().resolve()
        try:
            stdout = output_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise AnalysisError(f"Could not read Sherlock output: {exc}") from exc
        stderr = ""
        return_code = None
        invocation = []
        source_mode = "provided-output"
    else:
        stdout, stderr, return_code, invocation = run_sherlock(args)
        source_mode = "sherlock"

    findings = parse_findings(stdout)
    analyzed_at = utc_now()

    (case_dir / "sherlock-output.txt").write_text(stdout, encoding="utf-8")
    (case_dir / "sherlock-error.txt").write_text(stderr, encoding="utf-8")

    evidence = {
        "schema_version": 1,
        "username": args.username,
        "analyzed_at": analyzed_at,
        "source_mode": source_mode,
        "sherlock": {
            "command": invocation,
            "return_code": return_code,
            "timeout_seconds": args.timeout,
            "sites": args.site,
            "proxy_configured": bool(args.proxy),
            "output_file": "sherlock-output.txt",
            "error_file": "sherlock-error.txt",
        },
        "summary": {
            "candidate_count": len(findings),
            "platforms": [finding["site"] for finding in findings],
        },
        "findings": findings,
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
    if return_code not in (None, 0):
        print(
            f"Warning: Sherlock exited with code {return_code}; "
            "review sherlock-error.txt before relying on the results.",
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
        description="Run Sherlock and scaffold a public-source username analysis report."
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
        help="Parse an existing Sherlock stdout capture instead of running Sherlock.",
    )
    collect.add_argument(
        "--sherlock-command",
        help="Path to the Sherlock executable. Defaults to PATH or an importable module.",
    )
    collect.add_argument("--timeout", type=int, default=10, help="Per-site timeout in seconds.")
    collect.add_argument(
        "--job-timeout",
        type=int,
        default=1800,
        help="Overall Sherlock timeout in seconds (default: 1800).",
    )
    collect.add_argument("--site", action="append", default=[], help="Limit to a site; repeatable.")
    collect.add_argument("--proxy", help="Proxy URL passed through to Sherlock.")
    collect.add_argument("--print-all", action="store_true", help="Capture not-found and error rows.")
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
