**English** | [简体中文](README.zh-CN.md)

# Sherlock Skill

A Codex skill that turns a username search into an evidence-backed public
account map. It uses [Sherlock](https://github.com/sherlock-project/sherlock) to
find candidate profiles, then guides the agent through cross-platform
verification and preparation of a workspace report.

The key distinction is intentional:

```text
account exists  !=  account belongs to the same person
```

Sherlock supplies discovery signals. This skill adds evidence quality,
confidence, contradiction handling, privacy minimization, and a repeatable
report format.

## What it produces

```text
username_analysis/
└── <safe-username>/
    ├── username_analysis.md
    ├── evidence.json
    ├── sherlock-output.txt
    └── sherlock-error.txt
```

The Markdown report includes:

- scope and authorization
- candidate account URLs and public facts
- evidence tiers and cross-platform comparisons
- `Confirmed` / `Likely` / `Possible` / `Unrelated` / `Inconclusive` assessment
- a purpose-limited public profile summary
- identity and activity timeline
- login-required information gaps with legitimate verification routes
- sources, access dates, limitations, and next steps

The default language for the skill instructions and generated report is English.

## Safe scope

Use the skill for authorized assessments, personal profile cleanup, brand or
impersonation investigations, lawful due diligence, and research on consenting
subjects.

It is not designed for login bypass, private-data collection, credential or
session theft, harassment, locating or contacting a person, impersonation, or
high-impact eligibility decisions. Publicly visible information can still be
sensitive, so the report uses data minimization and separates facts from
inferences.

## Requirements

- Codex with skills enabled
- Python 3.10 or newer
- `sherlock-project` available on `PATH`

Install Sherlock with pipx:

```bash
pipx install sherlock-project
```

Test it:

```bash
sherlock --version
```

Network access and a local proxy may be required for GitHub-hosted Sherlock
data or blocked target sites.

The helper passes `--local` so a failed GitHub data-file fetch does not block
collection. The local site list may be older; record that limitation when
fresh coverage matters.

## Install the skill

Clone this repository directly into your Codex skills directory.

PowerShell:

```powershell
$target = Join-Path $HOME '.codex\skills\sherlock-skill'
git clone https://github.com/milddrunker/sherlock-skill.git $target
```

macOS or Linux:

```bash
git clone https://github.com/milddrunker/sherlock-skill.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/sherlock-skill"
```

Restart or refresh Codex if the skill is not discovered immediately.

## Use with Codex

Invoke the skill by name and state the research purpose and scope:

```text
Use $sherlock-skill to research the username "example_user" for an
authorized brand-impersonation review. Create the report in this workspace.
```

Codex will collect Sherlock candidates, inspect public pages, verify linkage,
complete the report, and run the validator.

## Use the helper directly

Create a case:

```bash
python scripts/username_analysis.py collect \
  --username example_user \
  --workspace .
```

If Sherlock is not on `PATH`, provide its executable:

```bash
python scripts/username_analysis.py collect \
  --username example_user \
  --workspace . \
  --sherlock-command /path/to/sherlock
```

If you already saved Sherlock output:

```bash
python scripts/username_analysis.py collect \
  --username example_user \
  --workspace . \
  --from-output sherlock-output.txt
```

Validate the completed report:

```bash
python scripts/username_analysis.py validate \
  username_analysis/example_user/username_analysis.md
```

Run `python scripts/username_analysis.py collect --help` for proxy, timeout,
site, and replacement options.

Run the repository tests:

```bash
python -m unittest discover -s tests -v
```

## Evidence rules

- A shared username alone is weak evidence.
- A `Likely` same-person conclusion requires at least two independent,
  non-generic overlaps and no material contradiction.
- Public profile existence, search ranking, and Sherlock output do not establish
  ownership.
- Blocked, stale, private, or login-gated pages are limitations, not negative
  findings.
- Login-only categories are documented by information type and legitimate
  route. The skill never asks for passwords, cookies, recovery codes, or one-time
  codes.

See
[references/identity-verification.md](references/identity-verification.md)
for the full confidence rubric and disclosure rules.

## Attribution and license

This project is independent from Sherlock and OSINTSearch. Sherlock is a
separate MIT-licensed project by Siddharth Dushantha and contributors.

This repository is released under the [MIT License](LICENSE).
