**English** | [简体中文](README.zh-CN.md)

# Sherlock Skill

An agent skill that turns a username search into an evidence-backed public
account map. It includes a standard-library scanner and a bundled site snapshot
from [Sherlock](https://github.com/sherlock-project/sherlock), then guides the
agent through candidate review, bounded follow-up searches from distinctive
public clues, cross-platform verification, and final integration into a
workspace report.

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
    ├── sherlock-scan.json
    ├── sherlock-output.txt
    └── sherlock-error.txt
```

The Markdown report includes:

- scope and authorization
- candidate account URLs and public facts
- pivot leads, search rounds, dead ends, and coverage of follow-up checks
- evidence tiers and cross-platform comparisons
- an integrated map of evidence-based clusters and unassigned candidates
- `Confirmed` / `Likely` / `Possible` / `Unrelated` / `Inconclusive` assessment
- a purpose-limited public profile summary
- identity and activity timeline
- login-required information gaps with legitimate verification routes
- sources, access dates, limitations, and next steps

All human-readable output defaults to English: the generated report, evidence
summaries, recommendations, limitations, and explanatory status text. The skill
does not infer language from the username or reviewed sources. Preserve handles,
URLs, source titles, and exact quoted labels; translate or paraphrase non-English
material in the surrounding analysis. A non-English request or conversation does
not change artifact language; only a direct instruction about the generated
document does. If the requester explicitly chooses another language, write the
report prose in that language and record the choice.

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

- Python 3.10 or newer
- Any agent that can execute the CLI or read `SKILL.md` / `AGENTS.md`
- Network access to target sites

No `pipx` or external `sherlock` installation is required. Validate the bundled
site snapshot:

```bash
python scripts/sherlock_scan.py validate-data
```

Network access or a proxy may still be needed for target sites. The bundled
481-site list is reproducible but may be older than upstream Sherlock; record
that limitation when fresh coverage matters.

## Install the skill

Clone the repository anywhere; there is no package installation step.

PowerShell:

```powershell
$target = Join-Path $HOME 'sherlock-skill'
git clone https://github.com/milddrunker/sherlock-skill.git $target
```

macOS or Linux:

```bash
git clone https://github.com/milddrunker/sherlock-skill.git \
  "$HOME/sherlock-skill"
```

For a skill-aware host, place or symlink this directory in that host's skills
directory and load `SKILL.md`. For a command-driven agent, point it to
`AGENTS.md` or `agent-manifest.json`. The CLI works independently of either
integration.

## Use with any agent

Give the agent the repository path and state the research purpose and scope:

```text
Read /path/to/sherlock-skill/SKILL.md and use its embedded scanner to research
the username "example_user" for an authorized brand-impersonation review.
Create the report in this workspace.
```

The agent will run the local scanner, inspect public pages, follow distinctive
public clues in bounded rounds when useful, verify linkage, integrate the
results, complete the report, and run the validator. Hosts that support
skill-name invocation can also expose the directory as `sherlock-skill`.

## Use the helper directly

Run the bundled scanner directly:

```bash
python scripts/sherlock_scan.py scan \
  --username example_user \
  --output username_analysis/example_user/scan.json
```

Create a case:

```bash
python scripts/username_analysis.py collect \
  --username example_user \
  --workspace .
```

If you already saved compatible scanner output:

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
- A display name, project, public link, or search result is a pivot lead, not
  proof of identity.
- A `Likely` same-person conclusion requires at least two independent,
  non-generic overlaps and no material contradiction.
- Weak clues are not propagated transitively; ambiguous accounts remain
  unassigned.
- Public profile existence, search ranking, and Sherlock output do not establish
  ownership.
- Blocked, stale, private, or login-gated pages are limitations, not negative
  findings.
- Login-only categories are documented by information type and legitimate
  route. The skill never asks for passwords, cookies, recovery codes, or one-time
  codes.

See
[references/identity-verification.md](references/identity-verification.md)
for the full confidence rubric and disclosure rules, and
[references/pivot-discovery.md](references/pivot-discovery.md) for the bounded
follow-up search procedure.

## Attribution and license

This project is independent from Sherlock and OSINTSearch. Sherlock is a
separate MIT-licensed project by Siddharth Dushantha and contributors.

This repository is released under the [MIT License](LICENSE).
