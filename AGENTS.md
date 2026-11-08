# Portable Agent Instructions

This repository is a self-contained, agent-neutral public-source research
workflow. It does not require a vendor-specific account or SDK, `pipx`, an API
key, or a separate Sherlock installation.

## Start

1. Read [`SKILL.md`](SKILL.md) before handling a real person's data.
2. Use the local Python CLI. Python 3.10 or newer and network access are the only
   runtime requirements.
3. For command discovery, read
   [`agent-manifest.json`](agent-manifest.json).

## Commands

Create the complete report workspace:

```bash
python /path/to/sherlock-skill/scripts/username_analysis.py collect \
  --username example_user \
  --workspace /path/to/workspace
```

Run only the username scanner:

```bash
python /path/to/sherlock-skill/scripts/sherlock_scan.py scan \
  --username example_user \
  --output scan.json
```

Restrict a scan or lower request pressure:

```bash
python /path/to/sherlock-skill/scripts/sherlock_scan.py scan \
  --username example_user \
  --site GitHub \
  --site Gitee \
  --timeout 10 \
  --workers 8
```

Validate the completed report:

```bash
python /path/to/sherlock-skill/scripts/username_analysis.py validate \
  /path/to/workspace/username_analysis/example_user/username_analysis.md
```

## Output Contract

The scanner writes UTF-8 JSON to stdout and, when requested, to `--output`.
Claimed accounts are under `results`; transport and WAF problems are summarized
in `summary` and, for compact output, `issues`.

The report helper creates:

```text
username_analysis/<safe-username>/
|-- username_analysis.md
|-- evidence.json
|-- sherlock-scan.json
|-- sherlock-output.txt
`-- sherlock-error.txt
```

## Operating Rules

- Public, lawful, and authorized research only.
- A shared username is not proof of identity.
- Never bypass login or collect passwords, cookies, recovery codes, or one-time
  codes.
- Keep site volume and concurrency modest; respect platform rules and retry
  limits.
- Record unknown, blocked, stale, and unavailable results as coverage limits.
- Do not send the scanned username or report to a third-party service
  automatically.
