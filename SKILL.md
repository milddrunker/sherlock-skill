---
name: sherlock-skill
description: Investigate a username across public sites with Sherlock, verify whether accounts belong to the same person, and generate a workspace report. Use for authorized public-source research; never for login bypass, private-data collection, harassment, or impersonation.
---

# Sherlock Skill

Turn a username into an evidence-backed public-account map without treating
same-name accounts as the same person.

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
- whether the output should be English or another language

The default report language is English. Create the case even when details are
partial, and record assumptions instead of inventing authorization.

## Workflow

1. Create the case and run Sherlock:

   ```bash
   python <skill-dir>/scripts/username_analysis.py collect \
     --username <username> \
     --workspace <workspace-root>
   ```

   Use `--from-output <captured-output>` when Sherlock output already exists.
   Use `--timeout 10` to limit slow sites. If the command is unavailable, show
   the installation error and ask before changing the environment.

   The helper passes `--local` to Sherlock so a failed GitHub data-file fetch
   does not block collection. Its site database may be older than upstream.
   Record that limitation when fresh site coverage matters; an operator can
   rerun Sherlock without `--local` after confirming network access.

   The helper creates:

   ```text
   username_analysis/<safe-username>/
   |-- username_analysis.md
   |-- evidence.json
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

4. Compare candidates using the evidence and confidence rules in
   [references/identity-verification.md](references/identity-verification.md).
   A shared username alone is weak evidence. Do not claim that accounts belong
   to one person unless the evidence meets the documented threshold.

5. Complete every section of `username_analysis.md`. Separate observable facts
   from inferences and keep source IDs attached to claims. Use neutral,
   non-stigmatizing language. Include contradictions and failed checks, not
   only convenient matches.

6. Describe login-required gaps by information category. Legitimate routes are
   an account owner's authorized export or interview and, where applicable, a
   platform's legal process. Never ask for passwords, session cookies, recovery
   codes, or one-time codes.

7. Validate the completed report:

   ```bash
   python <skill-dir>/scripts/username_analysis.py validate \
     <workspace-root>/username_analysis/<safe-username>/username_analysis.md
   ```

   Resolve every reported error and review any warning before delivery.

## Quality bar

- Find links vs. same-person linkage are distinct conclusions.
- Every material claim has a source, an access date, and a confidence level.
- At least one cross-platform, unique overlap is required for a `Likely`
  same-person conclusion.
- Missing, stale, blocked, or login-gated evidence is reported as a limitation.
- The final report answers the original question without adding unnecessary
  identifying detail.
- Outputs stay inside `username_analysis/` unless the user requests another
  location.
