# Investigation identity and versioning

## Purpose

This document defines the relationship between a long-lived Research Question (RQ) and a versioned Investigation that freezes one concrete research context.

It is subordinate to `0001_research_architecture.md`: Notion is authoritative for the mutable RQ catalog, while Git artifacts are authoritative for a frozen Investigation version.

## 1. RQ and Investigation are different identities

### Research Question (RQ)

An RQ is the long-lived identity of the question being pursued.

The RQ owns the stable conceptual intent of the question. Its Notion record may evolve operationally over time, but historical Investigations do not silently inherit those edits.

Example:

`RQ-0007`

### Investigation

An Investigation is one execution of an RQ under a specific frozen Research Context.

It records the question snapshot and the conditions under which evidence is selected, synthesized, and analyzed.

Example:

`RQ-0007-v001`

The same RQ may therefore have multiple Investigations:

- `RQ-0007-v001`
- `RQ-0007-v002`
- `RQ-0007-v003`

Each version is independently reproducible and historical versions remain interpretable after the Notion RQ changes.

## 2. Identifier format

### RQ ID

Canonical form:

`RQ-<NNNN>`

For v1, `NNNN` is exactly four decimal digits, zero-padded.

Regex:

`^RQ-[0-9]{4}$`

Examples:

- valid: `RQ-0001`
- valid: `RQ-0427`
- invalid: `RQ-7`
- invalid: `rq-0007`

If the project ever exceeds 9999 RQs, the identifier contract must be explicitly migrated rather than silently widening the format.

### Investigation ID

Canonical form:

`<RQ_ID>-v<VVV>`

For v1, `VVV` is exactly three decimal digits, starts at `001`, and increases monotonically per RQ.

Regex:

`^RQ-[0-9]{4}-v[0-9]{3}$`

Examples:

- `RQ-0007-v001`
- `RQ-0007-v002`

Version numbers MUST NOT be reused after they have been committed as a canonical Investigation.

## 3. Lifecycle and mutation rule

An Investigation version has two relevant phases for versioning.

### Draft context

Before the Research Context is frozen, the current Investigation version may be edited in place.

Typical allowed changes within the same draft version:

- refine question wording without changing RQ identity;
- fill previously unknown Scope or Significance;
- correct Question Type;
- refine investigation boundary;
- add missing context fields;
- fix errors discovered before the freeze point.

Unknown values are valid. A field that is not yet known remains absent or null according to its schema; no fabricated default is introduced merely to pass validation.

### Frozen context

The freeze point occurs when `00_context` is explicitly accepted as the baseline for evidence collection.

After this point, context-defining fields MUST NOT be changed in place.

If a context-defining field changes, allocate the next Investigation version.

Downstream artifacts (`10_evidence`, `20_synthesis`, `30_analysis`) are constructed under that frozen context. They may be iteratively refined during the same Investigation until the Investigation result is accepted.

After an Investigation result is accepted, substantive changes to the evidence snapshot or accepted analysis also require a new Investigation version. Historical accepted artifacts are not rewritten.

## 4. What causes a new Investigation version?

Assuming the underlying RQ identity remains the same, create a new Investigation version when any of the following changes after context freeze:

- the question snapshot changes semantically;
- Scope changes;
- Question Type changes;
- investigation boundary or inclusion/exclusion criteria change;
- time horizon / evidence cutoff changes when it affects eligible evidence;
- analytical assumptions that define the interpretation change;
- an accepted Investigation is reopened with substantively different evidence.

A new version is also required when a previously accepted result is recomputed under changed canonical inputs.

## 5. What does not cause a new Investigation version?

A new Investigation version is not required for:

- edits while the context is still draft;
- formatting-only changes;
- spelling or grammar corrections that provably do not change meaning;
- implementation refactoring of validators that does not change canonical inputs or outputs;
- regeneration of a derived rendering from unchanged canonical artifacts;
- Notion operational metadata changes that are not part of the frozen Research Context.

Git history still records implementation or formatting changes, but Investigation versioning is reserved for research-semantic changes.

## 6. Question wording rule

Question wording has two levels of change.

### Non-semantic wording change

If the set of admissible answers and the intended construct/estimand remain unchanged, the RQ identity remains the same.

Examples:

- grammar correction;
- terminology normalization;
- clearer phrasing with unchanged meaning.

For a draft Investigation, update in place.

For an already frozen Investigation, preserve the historical question snapshot. A future execution may use the updated wording in the next Investigation version, but the historical version is not rewritten.

### Semantic question change

If the change materially changes what would count as an answer, it is not merely an Investigation version change; it is a new RQ identity.

Indicators include a change to:

- target construct;
- population or unit of analysis when that is intrinsic to the question;
- causal treatment/comparator;
- outcome;
- prediction target;
- central mechanism being asked about.

When uncertain, prefer preserving the existing RQ and creating a new RQ only when the answer space has materially changed. Related RQs may be linked in Notion.

## 7. Scope change rule

Scope is Investigation-defining rather than RQ-identity-defining by default.

Before context freeze: update the same Investigation version.

After context freeze: allocate the next Investigation version.

If the Scope change is so large that it changes the conceptual question itself, create a new RQ instead.

## 8. Question Type change rule

Question Type selects or constrains the downstream analysis profile.

Therefore:

- before context freeze: update the same Investigation version;
- after context freeze: allocate the next Investigation version.

A Question Type change alone does not create a new RQ because it is an analytical classification, not the stable question identity.

## 9. Significance and other incomplete fields

Significance is allowed to be unknown.

The workflow MUST support an Investigation draft in which:

- Scope is unknown;
- Significance is unknown;
- some investigation-boundary details are pending.

Unknown is represented explicitly by omission or null according to the JSON Schema. Empty strings, placeholders such as `TBD`, and invented defaults are not canonical values.

A later Notion change to operational Significance does not retroactively modify a frozen Investigation. A new Investigation only snapshots the current value when a new execution is intentionally created.

## 10. Version allocation algorithm

For a new execution of an RQ:

1. Read the RQ ID.
2. Find the highest committed Investigation version for that RQ.
3. Allocate the next integer version, zero-padded to three digits.
4. Create the Investigation as draft.
5. Refine `00_context` until it is valid and explicitly frozen.
6. After freeze, context-defining semantic changes require the next Investigation version.
7. Never renumber historical Investigation versions.

Example:

If `RQ-0007-v001` and `RQ-0007-v002` exist, the next version is `RQ-0007-v003`, even if v002 was later abandoned.

## 11. Decision table

| Change | Draft context | Frozen context | RQ identity |
| --- | --- | --- | --- |
| Grammar-only wording correction | Same version | Preserve frozen snapshot; no rewrite | Same RQ |
| Semantically equivalent wording refinement | Same version | Next version for a new execution | Same RQ |
| Semantic question identity change | New RQ | New RQ | New RQ |
| Scope change | Same version | Next version | Usually same RQ |
| Question Type change | Same version | Next version | Same RQ |
| Fill unknown Scope/Significance | Same version | Preserve frozen snapshot; next version only if a new execution needs the new value | Same RQ |
| Add/refine evidence before result acceptance | Same version | Same version | Same RQ |
| Add substantive evidence after accepted result | N/A | Next version | Same RQ |
| Rendering/validator refactor only | Same version | Same version | Same RQ |

## 12. Invariant

An Investigation ID means:

> the RQ identified by the prefix, executed under the Research Context frozen for this version.

Therefore the same Investigation ID must never refer to two materially different frozen contexts.
