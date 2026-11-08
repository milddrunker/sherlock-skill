**English** | [简体中文](README.zh-CN.md)

# Sherlock Skill

<p align="center">
  <img src=".github/assets/social-preview.svg" alt="Sherlock Skill — multi-platform public social footprint and behavioral insight for security, brand protection, and privacy self-audits" width="100%">
</p>

**One username. A more complete public social footprint.**

[![CI](https://github.com/milddrunker/sherlock-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/milddrunker/sherlock-skill/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Runtime dependencies: 0](https://img.shields.io/badge/runtime_dependencies-0-brightgreen.svg)](#requirements)

Sherlock Skill helps you see the person behind a username. Start with one
handle, discover as many public accounts as possible across social, video,
community, creative, marketplace, and developer platforms, then connect only
the profiles supported by evidence.

The result is not another list of matching links. It is a source-backed view of
public interests, communities, activity patterns, possible account connections,
and the information that still cannot be confirmed.

Public-source, authorized research only.

## What you get

- **A wider public account map:** one search can surface profiles across
  different kinds of communities, not only developer or gaming sites.
- **Clearer account connections:** see which profiles have enough evidence to
  belong together, which are only possible matches, and which remain
  unconfirmed.
- **A public behavior profile:** summarize recurring interests, communities,
  projects, content style, and activity rhythm without turning inference into
  fact.
- **A reviewable evidence trail:** every material claim keeps its source,
  access date, confidence, and coverage limitation.

This does not guarantee exhaustive coverage. Private, login-gated, deleted,
blocked, unindexed, or differently named accounts may remain undiscovered.

## Who it is for

### Brand protection and trust teams

Find public accounts that may be linked to impersonation, lookalike profiles, or
brand misuse. Compare identity signals, keep contradictory evidence, and produce
a report another reviewer can follow.

### Security researchers and investigators

Start with a single handle, widen public coverage, and reduce the risk of
treating unrelated same-name accounts as one person.

### Personal privacy self-audit

See where your own username exposes public accounts and identifying details.
Use the report to identify over-sharing, account sprawl, and cleanup priorities.

Building an agent or internal research tool? The same workflow is available
through a portable CLI and machine-readable outputs; see
[Agent and developer integration](#agent-and-developer-integration).

## A typical investigation

1. **Start with a username.** Optionally provide an alias, target site list, or
   approved research question.
2. **Find public profiles.** Run the bundled scanner and follow distinctive
   public clues through a limited number of additional discovery checks.
3. **Separate discovery from identity.** Review each candidate and decide
   whether evidence supports connecting it to the same person.
4. **Summarize the public picture.** Group recurring interests, communities,
   roles, projects, and activity patterns with confidence labels.
5. **Keep the unknowns visible.** Document blocked pages, contradictions,
   stale evidence, and information that requires login or account-owner
   verification.

## Use with an agent

The simplest way to use the project is to give an agent the repository path,
the username, and the authorized purpose:

```text
Read /path/to/sherlock-skill/SKILL.md. Research "example_user" for an authorized
brand-impersonation review. Find public accounts, connect only those supported by
evidence, summarize public interests and communities, complete the report, and
run the validator.
```

The agent should keep public discovery separate from identity evidence, avoid
private or login-gated information, and leave ambiguous accounts unconfirmed.

## Install and run locally

### Requirements

- Python 3.10 or newer
- Windows, macOS, or Linux
- Network access to the sites being checked

### Create an analysis case

```bash
git clone https://github.com/milddrunker/sherlock-skill.git
cd sherlock-skill

python scripts/username_analysis.py collect \
  --username example_user \
  --workspace .
```

The helper scans the bundled 481-site snapshot and creates:

```text
username_analysis/example_user/
├── username_analysis.md
├── evidence.json
├── sherlock-scan.json
├── sherlock-output.txt
└── sherlock-error.txt
```

You can limit the scan to relevant platforms:

```bash
python scripts/username_analysis.py collect \
  --username example_user \
  --workspace . \
  --site Instagram \
  --site Reddit \
  --site YouTube \
  --timeout 10
```

Run `python scripts/username_analysis.py collect --help` for proxy, worker,
NSFW, and replacement options.

### Run the scanner only

```bash
python scripts/sherlock_scan.py scan \
  --username example_user \
  --output username_analysis/example_user/scan.json
```

### Validate a completed report

```bash
python scripts/username_analysis.py validate \
  username_analysis/example_user/username_analysis.md
```

## Agent and developer integration

The repository is agent-neutral and self-contained:

- [`SKILL.md`](SKILL.md) contains the full research and reporting workflow.
- [`AGENTS.md`](AGENTS.md) provides portable command-oriented instructions.
- [`agent-manifest.json`](agent-manifest.json) describes entrypoints and output.
- JSON scan output and the Markdown report are designed for downstream agents,
  review tools, and internal dashboards.

The scanner uses only the Python standard library. It supports site filtering,
bounded concurrency, HTTP/HTTPS proxies, and machine-readable results.

## Evidence model

| Conclusion | Minimum standard |
|---|---|
| Confirmed | Direct first-party or reciprocal public evidence uniquely connects the profiles |
| Likely | Two independent, non-generic overlaps with no material contradiction |
| Possible | One weak-to-moderate overlap and no contradiction |
| Unrelated | Evidence establishes distinct people or incompatible facts |
| Inconclusive | Evidence is insufficient, inaccessible, stale, or ambiguous |

A shared username, display name, or search ranking is a discovery signal, not
proof of account ownership. See
[identity-verification.md](references/identity-verification.md) for the full
rubric and [pivot-discovery.md](references/pivot-discovery.md) for the bounded
follow-up procedure.

## Safety and privacy

Use this project only when you have a lawful basis and appropriate scope for
public-source research. Representative uses include authorized security
assessments, personal profile cleanup, brand or impersonation investigations,
lawful due diligence, and research on consenting subjects.

This project is not a people finder and does not establish legal identity. Do
not use it to bypass authentication, collect private data, steal credentials or
sessions, harass or locate people, impersonate someone, or make high-impact
eligibility decisions.

Publicly visible information can still be sensitive. Keep reports limited to the
details needed for the authorized question, and do not publish credentials,
private research data, or unnecessary personal information.

## Compatibility and limitations

- Python 3.10+ is required.
- The scanner depends on public endpoints and may encounter CAPTCHAs, WAFs,
  rate limits, or client-side applications that cannot be read without a browser.
- The bundled 481-site snapshot is reproducible but may be older than upstream
  Sherlock.
- Scanner results are candidates, not verified account ownership.
- The validator checks structure, required conclusions, confidence, and
  unresolved scaffolding; it cannot prove that an analysis is correct.
- A behavior profile describes public activity; it is not a psychological
  diagnosis or a substitute for consent-based verification.

## Development

Run the test suite and validate the bundled site data:

```bash
python -m unittest discover -s tests -v
python scripts/sherlock_scan.py validate-data
```

Focused bug reports and pull requests are welcome. Keep changes within the
documented public-source and privacy boundaries.

## Documentation

- [Agent workflow](SKILL.md)
- [Portable command interface](AGENTS.md)
- [Programmatic manifest](agent-manifest.json)
- [Identity verification](references/identity-verification.md)
- [Bounded pivot discovery](references/pivot-discovery.md)
- [Technical note: discovery is not identity verification](docs/articles/username-search-is-not-identity-verification.md)

## License

This project is independently maintained and is not an official Sherlock
Project release. It is available under the [MIT License](LICENSE). Third-party
data and license notices are listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
