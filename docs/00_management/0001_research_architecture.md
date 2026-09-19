# Research architecture / authority boundary

## Purpose

This document is the canonical specification for responsibility and authority boundaries in the research-atelier workflow.

The system separates capture, frozen research artifacts, semantic construction, structural contracts, and deterministic enforcement so that the same fact is not independently maintained in multiple places.

## Authority model

| Concern | System / artifact | Responsibility | Authority |
| --- | --- | --- | --- |
| Discovery, capture, reusable catalog, operational current state | Notion | Research Topics, Research Questions, Sources, Evidence Notes, task state, operational metadata | Canonical for mutable operational state and reusable catalog records |
| Frozen investigation artifacts | Git JSON | Versioned Research Context, evidence snapshot, synthesis, analysis | Canonical for a frozen investigation version |
| Semantic construction and judgment | LLM | Construct structured synthesis, analytical judgments, proposed mappings | Not authoritative by itself; output becomes authoritative only after it is materialized in the designated canonical artifact and passes required validation/review |
| Structural contract | JSON Schema | Define allowed structure, required fields, types, enums, and conditional structure | Canonical contract for artifact structure |
| Deterministic enforcement | Python | Validate schema, references, IDs, version/path rules, deterministic invariants | Canonical executable enforcement of machine-checkable rules |

## Single-authority rule

Every information class MUST have exactly one canonical authority.

Derived copies MAY exist only as projections, snapshots, caches, or renderings. A derived representation MUST NOT become an independent editable authority.

When two representations conflict, the canonical authority defined here wins. The non-authoritative representation is regenerated, reconciled, or invalidated.

## Canonical ownership by information class

### Notion-authoritative

- Research Topic catalog and mutable topic metadata
- Research Question catalog and mutable operational metadata
- Source identity and bibliographic metadata
- Evidence Note source-faithful reusable notes
- Backlog / workflow status and other operational current state

### Git-artifact-authoritative

For one frozen Investigation version:

- Investigation / Research Context
- Evidence snapshot selected for that Investigation version
- Evidence-faithful synthesis
- RQ-specific analysis and Working Answer for that frozen version
- Artifact lineage and version identifiers stored in those canonical artifacts

### Contract-authoritative

- JSON Schema is authoritative for artifact shape.
- Python validation is authoritative for deterministic cross-artifact constraints that JSON Schema cannot express cleanly.

### Non-authoritative computational actors

- LLM output is a semantic proposal until written into the canonical artifact and validated.
- Rendered documents, summaries, dashboards, and Notion projections of Git results are derived views unless explicitly promoted by a later specification.

## Write-direction constraints

1. Notion catalog data may be snapshotted into a frozen Git Investigation artifact.
2. Git canonical analysis may later be projected back into Notion as operational current state, but that projection is derived unless a separate sync contract explicitly transfers authority.
3. A projection MUST carry enough provenance to identify the source Investigation version.
4. No field is manually maintained as authoritative in both Notion and Git.
5. Changes to an upstream canonical artifact invalidate dependent downstream artifacts until they are revalidated or regenerated.

## Role of docs/98_reusable_artifact

`docs/98_reusable_artifact` is reference / provenance material inherited from the earlier urban-legend workflow.

It is intentionally frozen as a reusable design reference. It is NOT the canonical specification for the new general Research workflow.

New Research specifications belong outside that directory, primarily under `docs/00_management` and the Research-specific schema / workflow locations established by subsequent tasks.

## Design consequence

The Research workflow is organized around:

`Evidence -> evidence-faithful structured representation -> analytical judgment`

The implementation responsibility split is:

`Notion = operational state`
`Git JSON = frozen canonical artifact`
`LLM = semantic construction / judgment`
`JSON Schema = structure contract`
`Python = deterministic enforcement`

This boundary is the prerequisite for Investigation versioning, canonical artifact design, validation, and Notion/Git projection rules.
