# Legacy Review schemas

> **DEPRECATED — historical compatibility only**
>
> Files in this directory MUST NOT be used to author a new Workflow 20 Review cycle.

This directory contains the pre-BKL-0034 single-file Review contract.

- `review_cycle.schema.json`: validates historical `report_type = semantic_review` single-file cycles.
- `review_common.schema.json`: retained definitions for legacy/compatibility references.

For a **new** Review cycle, use:

- `../review_manifest.schema.json`
- `../review_00_context.schema.json`
- `../review_10_evidence.schema.json`
- `../review_20_synthesis.schema.json`
- `../review_30_analysis.schema.json`
- `../review_layer_common.schema.json`

The top-level `../review_cycle.schema.json` and `../review_common.schema.json` files are deprecated compatibility redirects. Their continued existence does **not** make them current authoring schemas.

Historical canonical Review JSON must not be rewritten solely to migrate schema layout.
