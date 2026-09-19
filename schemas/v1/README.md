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
- `enum` is used only for closed vocabularies already defined by the architecture, such as Question Type and context state.
- Schema validation establishes structural validity, not semantic truth. Evidence-faithfulness and analytical correctness require later deterministic lineage checks and semantic review.

## 00_context

`00_context.schema.json` allows incomplete draft research context. Scope, Significance, and Question Type may be unknown.

A frozen context requires `frozen_at`.

## 10_evidence

`10_evidence.schema.json` stores the Investigation-specific evidence snapshot.

Each evidence item preserves Source provenance and an Evidence Note reference when one exists. `evidence_note` may be null for a directly snapshotted Source record.

The schema intentionally contains no Working Answer or analysis-judgment field.

## Fixtures

Fixtures live under `tests/fixtures/v1`.

- `*.valid.min.json` must pass its schema.
- `*.invalid.*.json` must fail for the named reason.

Task 08 will turn these contracts into repository-level deterministic validation.
