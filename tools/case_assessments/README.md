# Case assessment utilization tool (case-specific contract, v1)

This is **not a new canonical artifact or a Workflow 00/10/20 completion requirement**. It is a reusable optional projection for investigations using the frozen case/factor comparison contract of INV-000046. Other research types need their own contract or adapter.

## Files

- build.py: deterministic extraction, review/finalization gate, transitive K -> E -> Source lineage, completeness checks, JSON schema validation, regeneration check.
- case_assessments.schema.json: local output schema, not schemas/v2.
- case_assessments.template.json: structural template with placeholders (not a valid instance; do not commit filled placeholders).
- semantic_normalization.prompt.md, semantic_overlay.template.json, semantic_overlay.schema.json: optional semantic-only postprocessing, separate from deterministic result.

## Run from a Git checkout
Install jsonschema if needed. From repo root:

    python tools/case_assessments/build.py INV-000046
    python tools/case_assessments/build.py INV-000046 --check

The latest canonical Review must be PASS for the exact committed chain. The canonical projection log must be SUCCESS for that analysis blob. The tool invokes the existing through-30 validator and loads the canonical Review history helper. It uses the fixed framework RQ/INV/commit/blob from frozen Context, derives all IDs and factor definitions, then parses strict case sections, criterion lines and factor lines. Fail closed on format drift, incomplete/duplicate/out-of-order factors, missing references, different Review target or stale finalization. It never edits canonical inputs. Do not repair input text inside the generator to force success.

Output: investigations/<INV-ID>/derived/case_assessments.json. No wall-clock timestamp is generated; identical committed inputs produce identical bytes. The case count is discovered, not hardcoded. The four R1–R4 criteria are this particular contract; a different criterion contract requires an adapter/version, not an invented mapping. The exact source factor definition (including framework applicability and evidence classification) is retained in factor_framework; its K references belong to that framework Investigation, not the case Investigation.

## Semantics
- canonical_line and 1-based analysis_line are exact from reviewed working_answer.text (not JSON file line numbers).
- assessment_text preserves the entire clause including partial facts, unknowns, qualifiers and caveats. value repeats that clause only for applicable rows; null otherwise, with no deletion of the original text. limitations=null means not separately extracted, NOT absence of limitations.
- canonical_status is authoritative as a label from Analysis. Mapping 未知 to undetermined does not imply whether applicability itself or only the value is unknown. Mixed status retains the original subtask-specific wording. Reported is a row label, not a guarantee that every clause is an established fact.
- reference_role=confirmation_scope marks unknown/unconfirmed search coverage; K/E/Source links are transitive lineage and do not establish an affirmative fact. Other basis links preserve the original scope; case header source_refs is distinct from row trace.
- No numeric inference, reclassification, new evidence or semantic judgment occurs during generation.

## Optional semantic normalization
Use the prompt and overlay template only if a downstream use requires attribute decomposition. Supply the baseline bytes' SHA256 (e.g. sha256sum), explicit target keys and baseline JSON. Keep the resulting overlay as a separate non-authoritative artifact.

    python tools/case_assessments/build.py INV-000046 --overlay path/to/semantic_overlay.json

This verifies the exact baseline, schema and excerpt anchors; a human/semantic review must still verify meaning. Do not automatically merge or approve semantic overlay content. No overlay is needed for the current lossless baseline.

If a future Working Answer differs from this strict format, fail and either add a tested deterministic adapter or use a separately reviewed semantic extraction from accepted Analysis (with exact anchors). Never use the prompt to silently bypass a parser failure or edit canonical research results.

CSV is a projection of the resulting JSON (one row per case×factor), not another authority. 
