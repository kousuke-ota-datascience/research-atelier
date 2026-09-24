# Canonical Information Sources

This directory stores the Git-canonical metadata artifact for each reusable Information Source.

- One file per Source: `<Source ID>.json`
- Historical Source IDs remain `SRC-NNNN`.
- Sources allocated after BKL-0030 cutover use `SRC-NNNNNN`.
- Existing IDs are never renamed only to normalize width.
- The JSON filename must equal its `source_id`.
- Schema: `schemas/v2/information_source.schema.json`
- Validate with:

```bash
python -m research_atelier.validation.validate_information_source SRC-000120
```

Notion Sources remains the Source UID / Source ID allocation surface and human-facing catalog. After initial Git materialization, Information Source metadata in this directory is canonical. Investigation-specific access time and exact Source revision are frozen in `10_evidence.json`, not in this directory.
