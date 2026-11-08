# Username Search Is Discovery, Not Identity Verification

Username scanners are useful because they turn a single handle into a set of
public URLs. That output can look like a finished investigation. It is not.

A matching profile proves only that a URL responded when requested. It does not
prove who controls the profile, whether the page is current, or whether two
profiles with the same handle belong to the same person.

The distinction matters for security research, brand protection, due diligence,
and any workflow where an agent is expected to produce a reviewable result.

## Four assumptions that create bad findings

**A profile URL is an account.**  
Scanners can mistake redirects, generic app shells, WAF pages, or soft 404s for
successful profile responses. Every candidate needs a separate public-page
review.

**The same username is the same person.**  
Handles are reused, transferred, squatted, and chosen independently. A shared
username is a discovery signal, not ownership evidence.

**A search result is evidence.**  
A search ranking can explain how a candidate was discovered. It cannot establish
that two profiles belong to one person.

**A blocked page means the account does not exist.**  
CAPTCHAs, rate limits, regional restrictions, login walls, and client-side
applications are coverage gaps. They are not negative findings.

## A better evidence model

Start by separating the investigation into distinct layers:

1. **Discovery:** a scanner or search result identifies a possible candidate.
2. **Observation:** a public page exposes a fact such as a display name, public
   link, avatar, or activity date.
3. **Linkage evidence:** direct and non-generic evidence connects two profiles.
4. **Conclusion:** the evidence supports a defined confidence level.

A shared username is weak evidence. A distinctive public project or reciprocal
profile link may support closer review. Stronger cases require direct first-party
statements, reciprocal links, or evidence that uniquely connects the profiles.

Important details should carry a source ID, access date, and confidence level.
Contradictions and failed checks belong in the report because they explain how
the conclusion was reached.

## Bound the search

Open-ended expansion is a common failure mode in public-source research. A
display name can lead to a project, which leads to another profile, which leads
to an unrelated community, and soon the investigation has collected much more
information than the original question required.

Bounds reduce privacy risk and keep results reviewable:

- follow only distinctive, purpose-relevant public clues
- make at most two derived search rounds by default
- cap additional lead checks at 12 by default
- record every query, rejection, dead end, and blocked check
- stop when no round adds a candidate with meaningful linkage value

Following a clue does not create identity evidence. The source account and the
new candidate still require independent review.

## Do not propagate weak evidence

Transitive identity claims are especially fragile:

```text
Account A shares a display name with B.
Account B links to project C.
Account C appears with D.

Therefore A and D are the same person.  ← unsupported
```

Each link has a different evidence quality and may represent a different person,
organization, impersonator, or automated account. Clusters should require direct
evidence, not a chain of weak clues.

## Make the report auditable

A useful username report should show more than the final set of URLs. It should
make the reasoning reproducible:

- scope and authorization
- candidate status and public observations
- followed leads and bounded search rounds
- failed and blocked checks
- evidence tiers and contradictions
- integrated clusters and explicitly unassigned accounts
- source URLs, access dates, and limitations

This structure helps a reviewer challenge the conclusion without having to
repeat the entire investigation.

## Apply the same rules to agents

AI agents are good at collecting and organizing public information. They also
need explicit stopping conditions, evidence thresholds, and privacy boundaries.
An agent that can search indefinitely is not automatically producing better
research; it may simply be producing more unsupported linkages.

A practical agent workflow should preserve the distinction between:

```text
found a profile
reviewed a profile
found evidence connecting profiles
concluded that profiles belong to the same person
```

Those are four different outcomes and they should never collapse into one.

## A reference implementation

[Sherlock Skill](https://github.com/milddrunker/sherlock-skill) applies these
ideas in an agent-neutral workflow. It includes a local standard-library
username scanner, bounded pivot discovery, an identity-verification rubric,
structured evidence output, and report validation.

Use it only for authorized public-source research. It is not a people finder,
does not bypass authentication, and does not establish legal identity.
