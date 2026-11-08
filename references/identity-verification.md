# Identity Verification and Disclosure Rules

Use this reference when comparing candidate accounts or deciding how much
detail belongs in the report.

## Evidence quality

Assign each observation a source ID (`S1`, `S2`, ...) and classify it:

| Tier | Evidence | Typical effect |
|---|---|---|
| Strong | Reciprocal links between the exact profiles; first-party statement naming both accounts; verified ownership evidence voluntarily exposed on the profile | Can strongly support linkage |
| Moderate | Same distinctive handle plus matching distinctive avatar, biography, personal website, public name, or activity pattern across independent sites | Supports a `Likely` conclusion when independent |
| Weak | Same username, display-name similarity, generic avatar, similar interests, or similar posting time | Supporting context only |
| Contradictory | Different verified identities, incompatible dates, explicit statements, or mutually exclusive public facts | Reduces confidence or separates accounts |

Public page existence, search ranking, and Sherlock output are discovery
signals, not proof of ownership.

## Pivot clues and clusters

A pivot clue can explain how a candidate was discovered, but it is not identity
evidence by itself. When consolidating accounts:

- Keep the source candidate and source ID that exposed each clue.
- Treat a search result or newly discovered profile as a candidate, not a
  confirmed match.
- Require direct evidence for every account placed in a same-person cluster.
- Do not apply transitive closure to weak evidence.
- Leave accounts that share only a pivot clue, handle, generic interest, or
  timing in the unassigned section.

See [pivot-discovery.md](pivot-discovery.md) for the bounded search procedure.

## Conclusion rubric

- **Confirmed**: Direct first-party or reciprocal public evidence uniquely
  connects the profiles. Without account-owner verification, reserve this label
  for unusually strong public evidence and explain why.
- **Likely**: At least two independent, non-generic matches such as a unique
  cross-link plus a distinctive avatar or biography, with no material
  contradiction.
- **Possible**: One weak-to-moderate overlap and no contradiction. Do not merge
  the accounts into one identity.
- **Unrelated**: Evidence establishes distinct people or incompatible facts.
- **Inconclusive**: Evidence is insufficient, inaccessible, stale, or too
  ambiguous. This is the default when only the handle matches.

State confidence as High, Medium, or Low and include the decisive evidence and
the strongest contradiction. Never increase confidence solely because many
copies of the same handle or many results from one pivot were found.

## Useful comparison fields

Collect only when visible and relevant:

- display name and handle
- biography text
- reciprocal profile links
- public personal website and its ownership signals
- avatar visual description or stable public URL
- account creation date and public activity cadence
- stated interests, projects, or organizations
- platform verification status

Do not collect or infer:

- precise home or work location
- private contact information
- family or relationship details
- sexual orientation, health, religion, political affiliation, or other
  sensitive traits unless the authorized question specifically requires them
  and the use is lawful and proportionate
- passwords, recovery data, authentication secrets, or private messages
- data obtained by bypassing a login, paywall, consent screen, or platform rule

Location at country or region level is still potentially identifying and should
only appear when necessary and explicitly public.

## Login-required information

These categories normally require authenticated access, an authorized export
from the account owner, or a platform's lawful process:

| Category | What login may establish | Appropriate route |
|---|---|---|
| Account ownership | Current control, verified email or phone binding | Subject interview or platform verification |
| Private contact details | Email, phone, messaging identifiers | Account owner's voluntary disclosure |
| Private or friends-only posts | Content and activity history hidden from the public | Owner-authorized export |
| Direct messages and group chats | Communications and participant identity | Owner-authorized export or lawful platform process |
| Hidden connections | Followers, following, contacts, or membership lists | Owner-authorized export or lawful process |
| Private account metadata | Registration source, IP/login history, device history | Platform legal process only |
| Security state | MFA methods, recovery settings, active sessions | Account owner's security review |
| Legal identity | Government name or identity verification | Authorized verification process |

Do not frame these as "missing fields to fill" by technical means. Identify why
the information matters and who could lawfully confirm it.

## Report minimization

- Keep the report about the research question, not maximal information gain.
- Prefer aggregate observations over verbatim personal details.
- Do not repeat an incidental sensitive fact because it appeared in a source.
- Do not expose a private individual's contact path when the finding can be
  described without it.
- Mention account-status uncertainty whenever a platform page is ambiguous.
- Include how an account entered the investigation when that path affects how
  much confidence a reader might place in it.
- Retain only the sources needed to support conclusions, plus notes that future
  reviewers need to reproduce the assessment.
