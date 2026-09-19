# Notion <-> Git Projection Contract

## Purpose

This document defines the directional data contract between the Notion research databases and Git canonical Investigation artifacts.

There is no symmetric two-way synchronization.

The model is:

```text
Notion reusable catalog / operational state
        |
        | freeze selected state
        v
Git canonical Investigation artifacts
        |
        | project selected accepted outputs
        v
Notion operational current state
```

Authority always follows `0001_research_architecture.md`.

## 1. Authority summary

### Notion is authoritative for

- Research Topics catalog and topic relations
- current Research Question catalog state
- Source bibliographic identity / metadata
- reusable Evidence Notes
- mutable operational workflow state

### Git is authoritative for

For a specific Investigation version:

- frozen `00_context`
- frozen `10_evidence` snapshot
- `20_synthesis`
- `30_analysis`
- accepted Working Answer for that Investigation version

### Projection is never a second authority

A value copied across the boundary is either:

- a **snapshot** from Notion into a frozen Git artifact; or
- a **projection** from Git into a Notion display / operational property.

The copy does not create a second independently editable authority.

## 2. Notion -> Git: Research Question freeze

At creation of `00_context`, freeze the following Research Questions DB fields.

| Notion Research Questions property | Git 00_context field | Rule |
| --- | --- | --- |
| `RQ ID` | `rq_id` | Required identity |
| page URL | `question.notion_url` | Provenance reference |
| `Question` | `question.text` | Frozen wording snapshot |
| `Question Type` | `question_type` | Null allowed while draft |
| `Scope` | `scope` | Null allowed |
| `Significance` | `significance` | Null allowed |

The following Research Questions properties are **not** frozen into `00_context` by default:

- `Status`: operational Notion state;
- `Working Answer`: Git-derived projection target;
- `Topic`: catalog organization relation;
- `Parent Question`: catalog relation;
- `RQ UID`: Notion implementation identifier; `RQ ID` and page URL are sufficient for the canonical snapshot.

Investigation-specific boundary / assumptions are created in Git `00_context`; they are not written back into the RQ record as duplicate properties.

## 3. Notion -> Git: Evidence freeze

### Source / Evidence Note role

`Sources` and `Evidence Notes` are reusable Notion catalogs.

`10_evidence` is not a mirror of those databases. It is the Investigation-specific snapshot of selected evidence.

### Evidence Note mapping

For a selected Evidence Note:

| Notion Evidence Notes property | Git 10_evidence field | Rule |
| --- | --- | --- |
| page URL | `provenance.evidence_note.notion_url` | Stable provenance reference |
| `Evidence Note` | `content` and optional provenance title | Source-faithful note text |
| `Note Type` | `note_type` | Preserve note classification |
| `Location` | `source_locator` | Preserve source location |
| `Direct Quote` | `direct_quote` | Preserve exact quote when present |
| `Source` relation target URL | `provenance.source.notion_url` | Preserve Source lineage |

`10_evidence.evidence_id` is an Investigation-local lineage identifier used by `20_synthesis.evidence_refs`. It is not an independently maintained copy of the Notion `Evidence ID` formula.

### Source mapping

By default, Git stores only the minimum Source provenance needed to identify the Notion Source:

- Source page URL;
- optional Source title for readability.

The following Source fields remain Notion-authoritative and are not copied wholesale into `10_evidence`:

- `Source ID`
- `Source Type`
- `Journal / Publisher`
- `Authors`
- `Year`
- `URL`
- `DOI`
- `PDF / File`
- `Reading Status`
- `Reliability Note`
- `Research Questions` relation

This is intentional: the Investigation freezes the evidence content actually used, not a second bibliographic database.

If exact historical bibliography later becomes a reproducibility requirement, add an explicit citation snapshot contract rather than copying mutable Source fields ad hoc.

## 4. Fields that must not be duplicated as writable relations

The following relations remain authoritative only in Notion:

- Research Topics.`Parent Topic`
- Research Topics.`Research Questions`
- Research Questions.`Topic`
- Research Questions.`Parent Question`
- Sources.`Research Questions`
- Evidence Notes.`Source`

Git may contain immutable provenance references to the related Notion pages, but Git does not maintain a second mutable relationship graph.

Changes to those Notion relations do not retroactively rewrite historical Investigation artifacts.

## 5. Git -> Notion projection

### RQ.Working Answer

Decision: **project it from Git.**

The Notion Research Questions property `Working Answer` is a derived operational view of the latest accepted `30_analysis.working_answer.text` for that RQ.

Authority remains the accepted Git `30_analysis`.

Consequences:

- human edits to Notion `Working Answer` are non-canonical;
- the next successful projection may overwrite them;
- changing the canonical answer requires a new or revised Investigation analysis according to the versioning rules, not manual divergence in Notion.

### What v1 does not project

Git does not automatically project:

- `20_synthesis`
- individual judgments
- limitations
- unresolved questions
- Evidence snapshot contents
- Question Type / Scope / Significance back into Notion
- Source / Evidence Note records
- Topic or Source relations

Those remain available in Git and may later be rendered as derived views if useful.

### Research Question Status

`Status` remains Notion-authoritative operational state.

A successful Working Answer projection does not by itself force `Status = Answered`.

Workflow automation may later update Status only if that behavior is separately specified and tested.

## 6. Projection provenance

v1 does not add a new Notion property solely for projection provenance.

The projection operation must log at least:

- target RQ page URL;
- `rq_id`;
- source `investigation_id`;
- Git commit SHA containing the accepted `30_analysis`;
- projection timestamp;
- success / failure.

This preserves auditability without increasing Notion property count.

If the pilot shows that users need source Investigation visibility directly in Notion, add one dedicated provenance property later rather than embedding multiple duplicated fields.

## 7. Freeze transaction rule

A Notion -> Git freeze is considered successful only when:

1. the source Notion records were read;
2. the target Git artifact was materialized;
3. JSON Schema validation passed;
4. deterministic identity / lineage validation passed where implemented;
5. the complete target artifact was committed to Git.

A partially written artifact is not a valid snapshot.

If freeze fails, do not fabricate missing values and do not mutate the previous accepted Investigation.

## 8. Sync / projection failure rules

### Notion -> Git freeze failure

Before a new snapshot exists, Notion remains authoritative for current catalog state.

The failed / partial Git candidate is not canonical.

The previous committed Investigation remains canonical for its own historical version.

Retry from Notion current state or create the next Investigation version if the research context has changed.

### Git -> Notion projection failure

Git remains authoritative.

Notion `Working Answer` may be stale.

Do not change Git to match the stale Notion value.

Retry the projection from the accepted Git artifact.

### Apparent conflict between current Notion and historical Git

A changed current RQ in Notion and an older frozen Git context are not a synchronization conflict.

They are different temporal states:

- Notion = current mutable catalog
- Git = historical frozen Investigation

A new Investigation snapshots the new Notion state.

## 9. Source / Evidence Note update semantics

If a Source or Evidence Note changes in Notion after an Investigation has frozen `10_evidence`:

- the historical `10_evidence` remains unchanged;
- the Notion catalog reflects the current reusable record;
- a new analysis that should use the updated evidence creates or updates a not-yet-accepted Investigation according to the versioning rules;
- an already accepted Investigation that incorporates substantively changed evidence requires a new Investigation version.

## 10. Reliability Note boundary

`Sources.Reliability Note` is not automatically frozen as evidence content.

It is a mutable catalog-level assessment and may itself contain analyst judgment.

If a reliability concern materially affects the Investigation conclusion, express that effect explicitly in `20_synthesis` uncertainty or `30_analysis` limitation / judgment with traceable support. Do not silently copy the mutable Reliability Note into the evidence layer.

## 11. No reverse reconstruction rule

Git artifacts must not be used to reconstruct or overwrite the Notion catalog wholesale.

Specifically prohibited:

- generating Sources from `10_evidence` as if Git were the Source authority;
- generating Evidence Notes from `20_synthesis`;
- overwriting RQ Question / Scope / Question Type from historical `00_context`;
- rebuilding Notion relations from frozen Git references.

Projection is intentionally narrow.

## 12. Operational contract

The only v1 write-back from Git to the four research databases is:

```text
accepted 30_analysis.working_answer.text
    -> Research Questions.Working Answer
```

Everything else is either:

- Notion -> Git freeze;
- Git-only canonical research artifact;
- Notion-only reusable catalog / operational state.

This is the boundary that prevents dual authority.
