# Canonical Research Artifact Chain

## Purpose

This document defines the canonical artifact architecture for one Investigation.

The chain is:

`00_context -> 10_evidence -> 20_synthesis -> 30_analysis`

The central design constraint is that evidence-faithful representation and RQ-specific judgment are separate artifacts.

This generalizes the earlier urban-legend workflow, where source/content reconstruction was separated from analytical coding, while adding an explicit frozen Research Context layer.

## 1. Canonical directory layout

For Investigation `RQ-0007-v001`:

```text
investigations/
  RQ-0007-v001/
    00_context.json
    10_evidence.json
    20_synthesis.json
    30_analysis.json
```

These four JSON files are the canonical research artifacts for that Investigation version.

Derived Markdown, HTML, reports, dashboards, or Notion projections are not canonical unless a later contract explicitly says otherwise.

## 2. Global invariants

All four artifacts MUST identify the same `investigation_id`.

No downstream artifact may introduce source evidence that is absent from its upstream canonical artifact.

Every substantive analytical statement must be traceable through the chain:

`30_analysis judgment -> 20_synthesis knowledge unit -> 10_evidence evidence item -> Notion Source / Evidence Note provenance`

The chain is directional. Downstream artifacts may interpret upstream artifacts, but upstream artifacts must not be rewritten to fit downstream conclusions.

## 3. 00_context

### Responsibility

`00_context` freezes what is being investigated and under what conditions.

It is the Research Context baseline for the Investigation version.

### Write here

- `investigation_id`
- `rq_id`
- frozen question wording snapshot
- Question Type
- Scope
- Significance when known
- investigation boundary
- inclusion / exclusion constraints that define the investigation
- temporal boundary / evidence cutoff when applicable
- explicit assumptions that define the research setup
- context freeze state / provenance required by the schema

### Do not write here

- source excerpts or Evidence Notes
- evidence-derived claims
- synthesis conclusions
- agreement / conflict judgments across evidence
- Working Answer
- RQ-specific conclusion strength
- post-hoc interpretation invented during analysis

### Authority

This file is canonical for the frozen Research Context of this Investigation version.

It snapshots relevant Notion RQ state; later Notion edits do not mutate this historical context.

## 4. 10_evidence

### Responsibility

`10_evidence` is the exact Evidence snapshot used by this Investigation.

It is not a copy of all Notion Sources or all Evidence Notes. It is the selected, frozen evidence set that downstream artifacts are allowed to use.

### Write here

For each selected evidence item:

- stable evidence item ID within the Investigation
- Notion Evidence Note identifier / URL when available
- Source identifier / URL
- source-faithful extracted content or structured note
- source location / page / section / timestamp / other locator when available
- provenance needed to recover the original source record
- evidence status such as available / unavailable / superseded only when operationally necessary
- optional selection metadata that explains why the item is in this Investigation, without changing the evidence content

### Do not write here

- facts not present in the referenced source/evidence note
- cross-source synthesis
- adjudication of which source is ultimately correct
- Working Answer
- RQ-specific causal or explanatory conclusion
- unsupported paraphrases added to make evidence fit the hypothesis

### Selection is contextual; content is evidence-faithful

The decision to include an evidence item is Investigation-specific.

The content of the item must remain faithful to the source / Evidence Note. Selection does not authorize reinterpretation.

### Authority

Notion remains authoritative for reusable Source and Evidence Note catalog records.

`10_evidence` is authoritative for the frozen set and frozen representation actually used in this Investigation.

## 5. 20_synthesis

### Responsibility

`20_synthesis` converts the evidence snapshot into an evidence-faithful knowledge structure.

This is the general Research analogue of the urban-legend `contents` layer.

Its purpose is to make the evidence reusable and inspectable without collapsing immediately into the final RQ answer.

### Write here

- knowledge units supported by one or more `10_evidence` items
- normalized propositions or observations
- explicit relations among knowledge units
- agreement across evidence
- conflict / contradiction across evidence
- uncertainty and missing information
- source-reported causal claims, mechanisms, estimates, or interpretations, clearly represented as source-reported claims
- evidence boundaries and conditions
- lineage from every knowledge unit to supporting `evidence_id` values

### Do not write here

- the final Working Answer
- a decision about what the user should believe
- an RQ-specific overall causal conclusion unless that exact conclusion is itself a faithful representation of the source claim
- evidence not present in `10_evidence`
- hidden resolution of conflicts without retaining the conflicting evidence
- confidence values invented without a defined method

### Evidence-faithful means

A knowledge unit may normalize wording, merge redundant evidence, and expose relationships, but it must not add a proposition that cannot be reconstructed from its linked evidence.

When sources disagree, `20_synthesis` records the disagreement; it does not silently choose a winner.

When evidence is insufficient, uncertainty remains explicit.

## 6. 30_analysis

### Responsibility

`30_analysis` is the first artifact where RQ-specific analytical judgment is canonical.

It interprets the evidence-faithful synthesis in light of the frozen Research Context.

### Direct inputs

- `00_context`
- `20_synthesis`

`10_evidence` is available for traceability and audit, but a substantive claim in `30_analysis` must be mediated by a `20_synthesis` knowledge unit rather than bypassing the synthesis layer.

### Write here

- Working Answer
- RQ-specific interpretation
- analysis profile / Question Type-specific judgments
- strength and limits of the answer, when a defined method exists
- alternative explanations or competing interpretations
- limitations
- unresolved questions
- implications that are explicitly marked as analytical inference
- references to the `knowledge_unit_id` values that support each substantive judgment

### Do not write here

- new evidence absent from `10_evidence`
- new factual claims absent from `20_synthesis`
- source-faithful facts without lineage
- fabricated certainty
- hidden assumptions not represented in the analysis

### Boundary rule

If a statement answers "what does the evidence directly say or jointly establish as an evidence representation?", it belongs in `20_synthesis`.

If a statement answers "given this RQ and context, what conclusion should we draw from that evidence representation?", it belongs in `30_analysis`.

## 7. Dependency graph

```text
Notion RQ / Source / Evidence Note catalog
             |
             v
        00_context
             |
             v
        10_evidence
             |
             v
        20_synthesis
             |
             v
        30_analysis
```

For analytical reasoning, `30_analysis` also reads `00_context` directly so that Question Type, Scope, and investigation assumptions are explicit.

Thus the logical dependencies are:

- `10_evidence <- 00_context`
- `20_synthesis <- 10_evidence`
- `30_analysis <- 20_synthesis + 00_context`

## 8. Invalidation rules

Invalidation means that a downstream artifact can no longer be treated as validated/current until it is re-generated or re-reviewed against the changed upstream artifact.

### 00_context changes

If a context-defining field changes before freeze:

- update the same draft Investigation;
- any already-created `10_evidence`, `20_synthesis`, and `30_analysis` are invalidated.

After freeze, a context-defining change requires a new Investigation version under `0002_investigation_versioning.md`.

### 10_evidence changes

Any substantive addition, deletion, replacement, or content change in the evidence snapshot invalidates:

- `20_synthesis`
- `30_analysis`

Formatting-only or provenance-format changes that do not alter evidence identity/content do not require semantic invalidation, though deterministic validation must still pass.

### 20_synthesis changes

Any substantive knowledge-unit or relation change invalidates:

- `30_analysis`

A non-semantic serialization-only change does not require semantic re-analysis.

### 30_analysis changes

A change to `30_analysis` does not invalidate upstream artifacts.

It does require revalidation/review of `30_analysis` itself.

## 9. Invalidation matrix

| Changed artifact | 00_context | 10_evidence | 20_synthesis | 30_analysis |
| --- | --- | --- | --- | --- |
| 00_context | self | INVALID | INVALID | INVALID |
| 10_evidence | unchanged | self | INVALID | INVALID |
| 20_synthesis | unchanged | unchanged | self | INVALID |
| 30_analysis | unchanged | unchanged | unchanged | self |

"INVALID" means "must not be treated as current/accepted until rebuilt or revalidated."

## 10. No bypass rule

The following shortcuts are prohibited in canonical processing:

- Notion Evidence Note -> `30_analysis` without representation in `10_evidence` and `20_synthesis`
- external source -> `20_synthesis` without inclusion in `10_evidence`
- external source -> `30_analysis` directly
- Working Answer written back into `20_synthesis`
- analytical judgments inserted into `10_evidence` to justify downstream conclusions

This rule is what preserves auditability.

## 11. Minimal lineage identifiers

The v1 schemas should support at least the following references:

- `investigation_id` on every artifact
- `evidence_id` for each `10_evidence` item
- `knowledge_unit_id` for each `20_synthesis` unit
- `evidence_refs` from knowledge units to evidence items
- `knowledge_unit_refs` from analytical judgments to synthesis units

The exact schema is defined in Tasks 04 and 05.

## 12. Architectural consequence

The chain deliberately separates four questions:

1. `00_context`: What exactly are we investigating?
2. `10_evidence`: What evidence are we using?
3. `20_synthesis`: What can that evidence be represented as saying, including agreement, conflict, and uncertainty?
4. `30_analysis`: What do we conclude for this RQ under this context?

The Working Answer exists only at stage 30.
