---
name: sherlock-skill
description: Investigate a username across public sites, follow distinctive public clues in bounded pivot rounds, verify whether accounts belong to the same person, and generate an integrated workspace report. Use for authorized public-source research; never for login bypass, private-data collection, harassment, or impersonation.
---

# Sherlock Skill

Turn a username into an evidence-backed public-account map. When a reviewed
profile exposes a distinctive public clue, follow that clue through bounded
pivot rounds, then integrate all candidates without treating same-name accounts
as the same person.

This skill is portable across agent hosts: instructions are in this file and
[`AGENTS.md`](AGENTS.md), while [`agent-manifest.json`](agent-manifest.json)
describes the command interface. Do not depend on host-specific plugins or an
external Sherlock installation.

## Eligibility and boundaries

Use this workflow for authorized security assessments, personal profile
cleanup, brand or impersonation investigations, due diligence with a lawful
basis, or research on a consenting subject.

Do not use it to expose, intimidate, impersonate, locate, contact, or gain
access to a person; to target a minor; to collect login-only or private data;
or to make employment, credit, housing, insurance, or other high-impact
eligibility decisions. Public availability does not remove privacy risk.

## Inputs

Collect:

- the exact username or approved aliases
- the research purpose and authorization basis
- any sites that are explicitly in or out of scope
- whether the requester explicitly chose a language other than the default

## Output Language

All human-readable output defaults to English, including the generated report,
evidence summaries, recommendations, limitations, and explanatory status text.
Do not switch language merely because the username or a reviewed source uses
another language. Preserve handles, URLs, source titles, and exact quoted labels;
translate or paraphrase non-English source material in the surrounding English
analysis.

The language of the request, the surrounding conversation, or a filename is not
an explicit choice of document language. Only a direct request about the
generated report or other artifact changes the default. Conversational replies
may follow the requester's language while generated artifacts remain English.

Create the case even when details are partial, and record assumptions instead of
inventing authorization. If the requester explicitly chooses another language,
use it consistently for the human-readable report and record that choice in the
Scope and Authorization section.

## Workflow

1. Create the case and run the embedded scanner:

   ```bash
   python <skill-dir>/scripts/username_analysis.py collect \
     --username <username> \
     --workspace <workspace-root>
   ```

   Use `--from-output <captured-output>` when compatible output already exists.
   Use `--timeout 10` to limit slow sites. No `pipx` or external `sherlock`
   executable is required. The bundled 481-site snapshot may be older than
   upstream; record that limitation when fresh coverage matters.

   The helper creates:

   ```text
   username_analysis/<safe-username>/
   |-- username_analysis.md
   |-- evidence.json
   |-- sherlock-scan.json
   |-- sherlock-output.txt
   `-- sherlock-error.txt
   ```

2. Review every finding as a separate candidate. Open public pages read-only,
   without signing in, bypassing access controls, or sending messages. Keep
   requests modest and record an access date for each source.

3. Extract only purpose-relevant public facts: display name, bio, public links,
   avatar description, account creation date, public activity dates, and other
   fields voluntarily visible on the page. Never persist an incidental
   sensitive attribute, private contact detail, precise location, or private
   content.

4. Extract distinctive identity-bearing leads from reviewed profiles, such as an
   unusual exact display name, public project or domain, reciprocal profile link,
   or explicitly stated alias. Before following them, read
   [references/pivot-discovery.md](references/pivot-discovery.md). Search those
   leads through modest public checks and add any new profiles as separate
   candidates. The default budget is two derived rounds and 12 lead checks;
   record every query, result, rejection, and blocked check.

5. Do not use a pivot as evidence for itself. A display name or other clue can
   connect candidates for review, but same-person linkage still requires direct,
   non-generic evidence. Do not propagate weak evidence transitively between
   accounts that share different clues.

6. Compare candidates using the evidence and confidence rules in
   [references/identity-verification.md](references/identity-verification.md).
   A shared username alone is weak evidence. Do not claim that accounts belong
   to one person unless the evidence meets the documented threshold.

7. Consolidate the result into evidence-based clusters plus explicitly
   unassigned candidates. Complete every section of `username_analysis.md`,
   including the Iterative Discovery log and Integrated Account Map. Separate
   observable facts from inferences and keep source IDs attached to claims. Use
   neutral, non-stigmatizing language. Include contradictions, dead ends, and
   failed checks, not only convenient matches.

8. Describe login-required gaps by information category. Legitimate routes are
   an account owner's authorized export or interview and, where applicable, a
   platform's legal process. Never ask for passwords, session cookies, recovery
   codes, or one-time codes.

9. Validate the completed report:

   ```bash
   python <skill-dir>/scripts/username_analysis.py validate \
     <workspace-root>/username_analysis/<safe-username>/username_analysis.md
   ```

   Resolve every reported error and review any warning before delivery.

## Quality bar

- Find links vs. same-person linkage are distinct conclusions.
- Every followed clue has an origin, source, search round, outcome, and stop
  reason; generic or private clues were not used for expansion.
- Every material claim has a source, an access date, and a confidence level.
- At least one cross-platform, unique overlap is required for a `Likely`
  same-person conclusion.
- The final map assigns accounts only through direct evidence and leaves
  ambiguous candidates unassigned.
- Missing, stale, blocked, or login-gated evidence is reported as a limitation.
- The final report answers the original question without adding unnecessary
  identifying detail.
- Every human-readable deliverable follows the English-by-default language
  contract unless the requester explicitly chose another language.
- Outputs stay inside `username_analysis/` unless the user requests another
  location.
