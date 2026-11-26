# Optional semantic normalization — case assessment overlay

## Inputs
- Baseline JSON: {{CASE_ASSESSMENTS_JSON}}
- SHA-256 of baseline bytes (computed by a script): {{BASELINE_SHA256}}
- Target case/factor IDs (or explicit subset): {{TARGET_KEYS}}
- Output template: semantic_overlay.template.json
- Output schema: semantic_overlay.schema.json

## Task
Normalize only the requested already-reviewed assessment_text fields into a separate semantic overlay for downstream analysis. The baseline is immutable; this is a non-authoritative optional interpretation. Do not search sources, add new facts, reinterpret Evidence, improve judgments, or fill missing values. Do not alter applicability, epistemic_status, canonical_status, case eligibility, references, identifiers, or other baseline fields.

For each requested key:
1. Read the fixed factor definition, assessment_text and canonical_status together.
2. Separate explicit attributes from caveats; use narrowly named fields that retain task, scope, population, time basis, metric, and scenario distinctions. Use literal value_text, unit if literally stated (otherwise null), and an exact source_excerpt containing both the value and the unit. Use separate rows for observed vs estimated, pre vs post, or distinct subtasks. Do not calculate, convert units, infer denominators, make missing values false/zero, or translate a comparison into a new judgment.
3. Preserve limitations verbatim in limitations. If a clause is ambiguous or partly unknown, keep its exact wording; omit any attribute whose meaning cannot be separated safely. For mixed tasks do not merge non-applicable and unknown subtasks. A number in confirmation_scope does not establish the unknown attribute; only extract an explicitly stated partial fact with its limitation. For non-applicable rows, generally leave attributes empty.
4. Return only JSON matching semantic_overlay.schema.json; reuse the supplied ID and hash. Every value_text, source_excerpt, and limitation must be an exact substring of the relevant assessment_text. An empty entries array is valid when nothing can be safely normalized.

## Acceptance
Run build.py INV-ID --overlay <path>. The script checks identity, baseline hash, key uniqueness, excerpt containment and schema; this does not verify semantic correctness of field names or attribution. A separate human/semantic check is required before downstream use. Never merge the overlay into reviewed canonical artifacts or automatically replace the baseline.
