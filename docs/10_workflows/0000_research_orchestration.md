# Workflow 00 — Research Investigation Orchestration

## 0. Position

Workflow 00 is the top-level orchestration contract for one Research Investigation.

It decides:

- current Investigation state;
- the earliest safe resume point;
- whether downstream artifacts are stale after an upstream change;
- when Workflow 10 should run;
- when the Investigation may be finalized;
- whether the Git -> Notion Working Answer projection should be applied.

Workflow 00 does not recreate Source discovery, Evidence selection, Synthesis, or Analysis semantics. Those belong to Workflow 10.

It also does not reimplement JSON Schema or lineage validation. Those belong to the deterministic validator.

## 1. Public input

Normal business input is one Research Question or one Investigation ID.

When an RQ is supplied without an Investigation ID:

1. inspect existing Investigation versions;
2. decide whether the current work may resume an unfinished version;
3. otherwise allocate the next version according to `0002_investigation_versioning.md`.

Do not ask the user to provide internal artifact paths or validator stages when they can be derived.

## 2. Derived state model

The state is derived from current artifacts and validation results. It is not stored as a second authoritative status field.

### NEW

Definition:

- no `00_context.json` exists for the allocated Investigation.

Action:

- start Workflow 10 at context construction.

### PARTIAL

Definition:

- at least one canonical artifact exists;
- the existing contiguous prefix is valid;
- one or more downstream artifacts are missing.

Examples:

- 00 exists and passes; 10 is missing;
- 00 and 10 pass; 20 is missing;
- 00/10/20 pass; 30 is missing.

Action:

- resume at the earliest missing artifact.

### INVALID

Definition:

- an existing artifact fails deterministic validation; or
- a known upstream semantic change has invalidated a downstream artifact even if the downstream JSON remains schema-valid.

Action:

- find the earliest invalid artifact;
- repair/reconstruct from that stage;
- revalidate all downstream stages before they are trusted again.

### VALIDATED

Definition:

- 00, 10, 20, 30 all exist;
- `validate_investigation <ID> --through 30` returns PASS;
- no known upstream change has invalidated the current chain;
- finalization / accepted Working Answer projection has not yet been completed for the current analysis.

Action:

- perform the Workflow 10 completion check;
- if the analysis is accepted for the current Investigation, apply the projection contract.

### COMPLETE

Definition:

- all four canonical artifacts exist;
- through-30 deterministic validation returns PASS;
- Workflow 10 completion conditions hold;
- the current `30_analysis` is accepted as the current result for this Investigation;
- `30_analysis.working_answer.text` has been successfully projected to the corresponding Notion Research Question;
- no known upstream change remains unapplied.

A repeated Workflow 00 run should recognize COMPLETE and avoid rewriting canonical artifacts.

### BLOCKED

Definition:

Progress is impossible without resolving an external or semantic prerequisite, for example:

- RQ identity cannot be resolved;
- Investigation version ownership is ambiguous;
- required Notion/Git access is unavailable;
- Research Context cannot be made sufficiently definite to freeze without inventing assumptions;
- canonical contracts conflict in a way that cannot be resolved locally.

Action:

- stop and report the exact blocker;
- do not fabricate an artifact to escape BLOCKED.

### ERROR

Definition:

The workflow machinery itself cannot operate reliably, for example:

- schema cannot be loaded;
- validator returns ERROR;
- repository write fails in a way that leaves completion uncertain.

Action:

- stop;
- preserve the last known canonical state;
- do not reinterpret ERROR as research failure.

## 3. State derivation algorithm

For Investigation `ID`:

1. Check whether `investigations/ID/` and `00_context.json` exist.
2. If 00 is absent: state = NEW.
3. Validate through 00.
   - FAIL -> INVALID at 00.
   - ERROR -> ERROR.
4. If 10 is absent: PARTIAL, resume 10.
5. Validate through 10.
   - FAIL -> INVALID at the earliest reported 00/10 error.
   - ERROR -> ERROR.
6. If 20 is absent: PARTIAL, resume 20.
7. Validate through 20.
   - FAIL -> INVALID at the earliest reported 00/10/20 error.
   - ERROR -> ERROR.
8. If 30 is absent: PARTIAL, resume 30.
9. Validate through 30.
   - FAIL -> INVALID at the earliest reported stage.
   - ERROR -> ERROR.
10. If all pass: VALIDATED.
11. Check whether the current analysis has already completed accepted-result projection.
   - yes -> COMPLETE;
   - no -> finalize/project, then COMPLETE on success.

The validator result is evidence about deterministic validity; it is not a semantic quality score.

## 4. Earliest-resume rule

Always resume from the earliest artifact that is:

1. missing;
2. deterministically invalid;
3. semantically invalidated by a changed upstream artifact.

Examples:

| Current fact | Resume |
| --- | --- |
| no artifacts | 00 |
| 00 PASS, 10 missing | 10 |
| 00/10 PASS, 20 missing | 20 |
| through20 PASS, 30 missing | 30 |
| 10 changed after 30 existed | re-evaluate 20, then 30 |
| 20 changed | re-evaluate 30 |
| 30 only changed | validate/finalize 30 |

Do not restart from 00 merely because the workflow is re-run.

## 5. Invalidation rule

Dependency:

`00_context -> 10_evidence -> 20_synthesis -> 30_analysis`

If an upstream artifact changes semantically:

| Changed artifact | Treat as stale until re-evaluated |
| --- | --- |
| 00 | 10, 20, 30 |
| 10 | 20, 30 |
| 20 | 30 |
| 30 | 30 only |

A downstream file may remain byte-for-byte present but still be **invalidated**.

Therefore file existence alone never proves currency.

When a context-defining change occurs after freeze or an accepted result is substantively reopened, apply the Investigation versioning contract instead of rewriting history.

## 6. Near-idempotent rerun rules

A rerun should converge on the same canonical state when inputs have not changed.

Rules:

- do not allocate a new Investigation version merely because Workflow 00 was invoked again;
- do not regenerate a PASS artifact when no upstream input changed and no semantic correction is required;
- do not rewrite files solely to refresh timestamps;
- do not renumber E/K/J identifiers without a semantic reason;
- do not project Working Answer again when Notion already equals the accepted current Git answer;
- if projection is stale, update only the derived Notion Working Answer, not Git;
- validation may be safely repeated because it is deterministic.

Idempotence is "near" rather than absolute because external evidence discovery and explicit researcher decisions may legitimately change inputs.

## 7. Finalization and Working Answer projection

When state reaches VALIDATED:

1. verify Workflow 10 completion conditions;
2. confirm no known evidence/context change is pending;
3. designate the current `30_analysis` as accepted for this Investigation;
4. project `30_analysis.working_answer.text` to Notion `Research Questions.Working Answer`;
5. log target RQ, Investigation ID, Git commit SHA, timestamp, and success/failure as required by `0006_notion_git_projection_contract.md`;
6. if projection succeeds, state becomes COMPLETE;
7. if projection fails, Git remains authoritative and state remains VALIDATED until projection succeeds.

The projection step is narrow; Workflow 00 does not synchronize the rest of the Notion databases back from Git.

## 8. MVP exclusions

The MVP does **not** require:

- independent semantic Review workflow;
- Review sequence numbers;
- review-target SHA freeze;
- Git ancestry control-plane logic;
- SHA synchronization into Notion;
- a persistent orchestration state machine;
- automatic Notion Status changes;
- Workflow 90-style control-plane reconciliation.

These may be introduced only after the E2E pilot demonstrates a concrete need.

Git commits remain normal provenance, but no dedicated SHA control plane is a prerequisite for COMPLETE in the MVP.

## 9. Completion report

A Workflow 00 run should report at minimum:

- `investigation_id`;
- derived state: NEW / PARTIAL / INVALID / VALIDATED / COMPLETE / BLOCKED / ERROR;
- earliest resume stage when not COMPLETE;
- latest deterministic validation result;
- whether any downstream artifact is invalidated;
- whether Working Answer projection is current;
- blocker/error details when applicable.

## 10. Invariant

Workflow 00 is an orchestrator, not an alternate source of truth.

It derives state from:

- canonical Git artifacts;
- deterministic validation;
- the authority/versioning/projection contracts;
- current Notion catalog state only where that catalog is authoritative.

It must never make an old downstream artifact trusted merely because the file exists.
