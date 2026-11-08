# Bounded Pivot Discovery

Use this reference after the initial username scan when a reviewed public
profile contains a distinctive clue that could reveal additional accounts. A
pivot broadens discovery; it does not lower the identity-linkage threshold.

## Core principle

Treat every derived clue as a search key, not as an identity claim.

```text
public clue -> new candidate -> separate review -> possible linkage
```

The report must preserve this chain. A display name, project name, or search
result does not become evidence that two accounts belong to one person merely
because a search connected them.

## Lead selection

Prefer leads that are both purpose-relevant and discriminating:

- an exact, unusual display name
- an uncommon biography phrase
- a public project, repository, organization, or domain name
- a public personal website or reciprocal profile link
- another username or alias explicitly stated on the reviewed profile
- a distinctive avatar description used across independent platforms

Do not pivot on:

- generic names such as a common given name or one-word handle fragments
- common interests, similar posting times, or default avatars
- private email addresses, phone numbers, messaging identifiers, or precise
  locations
- sensitive traits, private activity, or login-gated information
- breach data, paid people-search data, or leaked records

If a common personal name is the only lead and the research goal cannot be met
without it, narrow the search with an already-public project, organization, or
profile context. Do not add unrelated personal details to make the query
unique.

## Search budget

Use a bounded search rather than open-ended expansion:

- default to at most two derived rounds beyond the initial username scan
- perform at most 12 additional public lead checks across those rounds
- deduplicate leads after normalization
- stop when a full round adds no new candidate with at least weak-to-moderate
  linkage value
- stop immediately when the purpose is answered or the authorized scope ends

Expand beyond the default budget only when the original purpose and
authorization clearly justify it and the additional scope is explicit.

## Round procedure

1. Select one or a small batch of high-value leads from reviewed candidates.
   Record the source ID that exposed each lead.
2. Normalize the lead and record the exact public query or platform check.
   Keep rare phrases quoted when appropriate.
3. Review public results without signing in or bypassing access controls. Add
   each new profile as a new candidate with a `P001`, `P002`, ... ID and its
   discovery round; do not overwrite the original `F...` candidate list.
4. Review each new candidate independently. Separate page existence, observed
   attributes, and inferred linkage.
5. Extract further leads only from a candidate that has itself been reviewed.
   Avoid cycles and rechecking the same normalized clue.
6. Record failed, blocked, generic, and irrelevant results. They are important
   for showing why the trail stopped.
7. After the final round, consolidate all candidates into evidence-based
   clusters and unassigned accounts.

When maintaining `evidence.json`, retain the scaffolded
`discovery.strategy` and `discovery.limits`. Add one object to
`discovery.candidates` per profile first found through a pivot, including its
`P...` ID and discovery round. Add one object to `discovery.leads` per
normalized clue, including `id`, `origin_candidate`, `type`, `value`, `source`,
`why_discriminating`, `scope`, and `status`. Add one object to
`discovery.rounds` per check or coherent batch, including the round number,
seed, query or platform check, outcome, decision, and source IDs. Add
evidence-based groups to `discovery.clusters`; do not place an account there
unless its member accounts meet the normal linkage threshold. Record blocked
and rejected leads rather than deleting them.

## Example

An initial profile exposes the exact, uncommon display name
`EXAMPLE-UNIQUE-DISPLAY-NAME`.

1. Record the reviewed profile as the lead origin, citing its source ID.
2. Search the exact phrase publicly and review promising pages read-only.
3. Add any new profiles as additional candidates, even if they expose no
   matching handle.
4. Merge them only if direct evidence crosses the normal threshold, such as the
   exact rare display name plus the same public project link, or a reciprocal
   profile link. The display name alone is not enough.
5. If no new vetted match appears, retain the display name as an investigated
   lead and mark the trail exhausted rather than treating it as proof.

## Final integration

Create an integrated account map with one row per evidence-based cluster and
explicit rows for unassigned candidates.

- Use direct observations to place an account in a cluster.
- Do not apply transitive closure to weak clues. If A and B share a clue and B
  and C share a different clue, that does not automatically link A and C.
- A shared pivot can create a candidate group, but not a same-person conclusion.
- Keep contradictory evidence with the cluster and reduce confidence when it
  is material.
- State which accounts remain unassigned and why.
- Include lead count, completed rounds, exhausted leads, and unresolved checks
  in limitations.
