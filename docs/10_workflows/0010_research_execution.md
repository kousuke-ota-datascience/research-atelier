# Workflow 10 — Execute one Investigation

## 0. Position

This workflow is the canonical execution procedure for constructing one Research Investigation from frozen context through deterministic validation of `30_analysis`.

It defines **execution order and semantic construction rules**.

It does not redefine JSON fields, required properties, enums, or reference formats. Those are defined by `schemas/v1`.

Deterministic checks are delegated to:

`python -m research_atelier.validation.validate_investigation <Investigation_ID> --through 00|10|20|30`

Semantic construction remains an LLM / researcher responsibility.

## 1. Input and output

### Input

- one allocated `Investigation_ID`, e.g. `RQ-0007-v001`;
- the corresponding Notion Research Question;
- access to the reusable Notion Sources / Evidence Notes catalogs.

### Canonical output

```text
investigations/<Investigation_ID>/
  00_context.json
  10_evidence.json
  20_synthesis.json
  30_analysis.json
```

## 2. Responsibility boundaries

### Source discovery

Purpose: find candidate sources relevant to the frozen Research Context.

Source discovery may add or refine reusable records in Notion Sources / Evidence Notes. It does not directly create analytical conclusions.

Priority should follow the research question: primary evidence, original data, official specifications, original papers, or other direct sources are preferred when they are the appropriate evidence class.

Absence of a high-authority source must remain visible; lower-quality evidence is not silently promoted.

### Evidence selection

Purpose: decide which source-faithful Evidence Notes / direct source observations are included in this Investigation.

Selection is RQ/context-specific. Evidence content is not rewritten to make it support the desired answer.

`10_evidence` freezes only selected evidence and provenance; it does not become a second bibliographic database.

### Synthesis

Purpose: construct an evidence-faithful knowledge representation from `10_evidence`.

Synthesis may normalize wording, group evidence, expose agreement/conflict/uncertainty, and make relations explicit.

It must not silently adjudicate conflict or introduce the final Working Answer.

### Analysis

Purpose: interpret `20_synthesis` for the frozen RQ/context.

Analysis uses the Question Type profile defined in `0009_analysis_profiles.md`.

This is the first stage where RQ-specific judgments and Working Answer are canonical.

## 3. Execution sequence

### Step 0 — Preflight

1. Resolve the RQ corresponding to the Investigation prefix.
2. Confirm the Investigation ID follows `RQ-NNNN-vVVV`.
3. Confirm the version has not already been used for a materially different frozen context.
4. Load the authority, versioning, artifact-chain, projection, and profile contracts.
5. If an existing Investigation directory exists, inspect its current artifact stage before writing.

Stop if identity or version ownership is ambiguous.

### Step 1 — Construct and freeze `00_context`

1. Snapshot the Notion RQ fields specified by the projection contract.
2. Add Investigation-specific boundary and assumptions when known.
3. Keep unknown Scope / Significance / profile-relevant context null or absent; do not invent defaults.
4. Before freeze, refine the draft until the intended research boundary is sufficiently explicit.
5. Set `context_state = frozen` and `frozen_at`.
6. Run:

```bash
python -m research_atelier.validation.validate_investigation <ID> --through 00
```

7. Do not proceed on FAIL / ERROR.
8. Commit `00_context.json` as the context baseline.

After this point, context-defining semantic changes require the versioning rules in `0002_investigation_versioning.md`.

### Step 2 — Discover Sources and capture reusable Evidence Notes

1. Search for evidence relevant to the frozen question, scope, and investigation boundary.
2. Add reusable Source records to Notion rather than directly embedding ad-hoc bibliography into Git.
3. Capture source-faithful Evidence Notes with location / quote where useful.
4. Track contradictory evidence and null results; do not select only confirming material.
5. Distinguish source claims from the analyst's own inference.
6. Stop searching when the Investigation has enough evidence to address the scoped question **or** further search is no longer justified by expected information gain / resource constraints.
7. Record important evidence gaps explicitly rather than filling them by inference.

Source discovery is iterative; a new relevant source may return this step to active status before the Investigation is accepted.

### Step 3 — Select and freeze `10_evidence`

1. Select the evidence actually used for this Investigation.
2. Assign Investigation-local `E####` IDs.
3. Preserve Notion Source / Evidence Note provenance according to the projection contract.
4. Preserve exact uncertainty and qualification from the source.
5. Do not add cross-source synthesis, causal judgment, or Working Answer.
6. Run validation through 10.
7. Do not proceed on FAIL / ERROR.
8. Commit `10_evidence.json` independently.

If the selected evidence set changes substantively later, `20_synthesis` and `30_analysis` become invalid.

### Step 4 — Construct `20_synthesis`

1. Use only evidence present in `10_evidence`.
2. Create stable `K####` knowledge units with `evidence_refs`.
3. Represent agreement, conflict, qualification, dependency, association, and uncertainty where supported.
4. Keep source-reported explanations distinguishable from the workflow's own analytical conclusions.
5. Preserve unresolved conflict rather than forcing one source to win.
6. Do not place the Working Answer in this artifact.
7. Run validation through 20.
8. Do not proceed on FAIL / ERROR.
9. Commit `20_synthesis.json` independently.

If evidence changes, rebuild/revalidate synthesis before analysis.

### Step 5 — Construct `30_analysis`

1. Read the frozen `00_context` and validated `20_synthesis`.
2. Select the profile that matches `question_type`.
3. Fill only profile fields that are known and applicable.
4. Form RQ-specific judgments, limitations, alternatives, unresolved questions, and Working Answer.
5. Every substantive judgment must trace to one or more `K####` units where the schema requires it.
6. Do not bypass synthesis by inserting raw Evidence references into analysis judgments.
7. Distinguish facts represented in synthesis from new analytical inference.
8. Do not convert association into causation, predictive performance into mechanism, or conceptual coherence into empirical support.
9. Run validation through 30.
10. Do not proceed on FAIL / ERROR.
11. Commit `30_analysis.json` independently.

## 4. Evidence insufficiency rule

Insufficient evidence is a valid research outcome; fabricated completion is not.

Stop semantic construction at the earliest stage that cannot be supported:

- if context is too ambiguous to define an Investigation, stop before freeze;
- if no usable evidence can be established, do not invent `10_evidence` content;
- if evidence cannot support a knowledge unit, do not invent `20_synthesis`;
- if synthesis cannot support a substantive answer, do not infer one.

When the useful result is specifically "the available evidence is insufficient", `30_analysis` may state that as the Working Answer **only if** the evidence-search boundary and relevant gaps are explicit and the answer does not smuggle in an unsupported substantive conclusion.

## 5. Upstream change / invalidation handling

Before editing an upstream canonical artifact, determine whether the versioning rule permits in-place change.

Within a not-yet-accepted Investigation:

- change to `00_context` invalidates 10, 20, 30;
- change to `10_evidence` invalidates 20, 30;
- change to `20_synthesis` invalidates 30;
- change to 30 invalidates only 30 itself.

After an accepted Investigation, changes governed by the versioning contract create a new Investigation version rather than rewriting historical accepted artifacts.

"Invalid" means the downstream artifact must not be treated as current until reconstructed or explicitly revalidated against the new upstream state.

## 6. Deterministic validation rule

Run the public CLI, not internal validator functions, at each stage.

Expected machine-readable result:

- `PASS`: deterministic structure / identity / reference rules pass;
- `FAIL`: artifact content violates a deterministic rule;
- `ERROR`: validation infrastructure / schema configuration could not run reliably.

Only PASS permits progression to the next canonical artifact.

A PASS does **not** mean the semantic analysis is scientifically correct.

## 7. Git rule

Canonical artifact changes are committed at artifact boundaries.

Preferred sequence:

1. validated `00_context`
2. validated `10_evidence`
3. validated `20_synthesis`
4. validated `30_analysis`

Do not combine unrelated workflow refactoring with an Investigation artifact commit.

Git history is provenance, but the artifact contents and validation contract remain the research-state canon.

## 8. Completion condition

Workflow 10 is complete when:

- `00_context` is frozen;
- selected `10_evidence` is source-faithful;
- `20_synthesis` preserves evidence lineage, disagreement, and uncertainty;
- `30_analysis` uses the correct Question Type profile;
- validation through 30 returns PASS;
- the four artifacts are committed;
- no known upstream change has left a downstream artifact invalid.

Projection of an accepted Working Answer to Notion is governed by the projection contract and orchestration workflow, not by artifact construction itself.
