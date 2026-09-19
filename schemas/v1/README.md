# Schema v1 contract

This directory contains the canonical JSON Schema Draft 2020-12 contracts for Research Atelier artifacts.

## Policy

- `schema_version` is required and fixed by `const` for each schema revision.
- `artifact_type`, `investigation_id`, and `rq_id` are required identity fields.
- IDs use the formats defined in `docs/00_management/0002_investigation_versioning.md`.
- Cross-field invariants that standard JSON Schema cannot express cleanly, such as `investigation_id` having the same RQ prefix as `rq_id`, are enforced by the deterministic Python validator.
- `additionalProperties: false` is the default for canonical artifact objects so accidental fields do not silently become part of the contract.
- `required` contains only fields needed to identify the artifact and preserve its minimum semantics.
- Unknown values are represented by omission or explicit `null` only where the schema allows it. Empty strings, `TBD`, and invented defaults are not canonical unknown values.
- `enum` is used only for closed vocabularies already defined by the architecture, such as Question Type, context state, Evidence Note type, and synthesis relation type.
- Schema validation establishes structural validity, not semantic truth. Evidence-faithfulness and analytical correctness require deterministic lineage checks and semantic review.

## 00_context

`00_context.schema.json` allows incomplete draft research context. Scope, Significance, and Question Type may be unknown.

A frozen context requires `frozen_at`.

## 10_evidence

`10_evidence.schema.json` stores the Investigation-specific evidence snapshot.

Each evidence item preserves Source provenance and an Evidence Note reference when one exists. `evidence_note` may be null for a directly snapshotted Source record.

For Evidence Notes, v1 can freeze the source-faithful note text, `Note Type`, `Location`, and `Direct Quote`. Source bibliographic metadata remains Notion-authoritative and is not copied wholesale into the Investigation artifact.

The schema intentionally contains no Working Answer or analysis-judgment field.

## 20_synthesis

`20_synthesis.schema.json` stores evidence-faithful knowledge units.

Every knowledge unit has a stable `knowledge_unit_id` and one or more `evidence_refs`.

Cross-unit agreement and conflict are represented by `relations[].relation_type`. Uncertainty is explicit in the `uncertainties` collection. A Working Answer is intentionally invalid in this artifact.

## 30_analysis

`30_analysis.schema.json` is the first schema that contains RQ-specific analytical judgment.

The common v1 schema contains:

- the Question Type discriminator;
- Working Answer;
- analytical judgments;
- limitations;
- unresolved questions;
- optional alternative interpretations;
- lineage to Synthesis via `knowledge_unit_refs`.

It intentionally does **not** contain raw `evidence_refs` on analytical judgments. Evidence lineage is transitive:

`30_analysis -> knowledge_unit_ref -> 20_synthesis.evidence_refs -> 10_evidence`

This prevents analysis from bypassing the synthesis layer.

### Question Type-specific fields

The common v1 schema contains only the `question_type` discriminator. Question Type-specific payload fields are intentionally out of scope for this core schema.

Task 09 will define Analysis Profiles and decide whether they are composed as companion schemas, conditional schema fragments, or a later schema revision. Until then, no ad-hoc Question Type-specific fields are allowed in canonical `30_analysis`.

## Fixtures

Fixtures live under `tests/fixtures/v1`.

- `*.valid.min.json` must pass its schema.
- `*.invalid.*.json` must fail for the named reason.

Task 08 will turn these contracts into repository-level deterministic validation, including cross-artifact reference existence and identity invariants.
