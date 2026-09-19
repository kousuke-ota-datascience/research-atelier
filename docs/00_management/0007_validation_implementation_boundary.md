# Validation implementation boundary

## Canonical Research namespace

The canonical implementation for general Research validation is:

`src/research_atelier/validation/`

The generic core currently provides:

- deterministic JSON parsing;
- Draft 2020-12 JSON Schema validation;
- stable validation issue/result data structures;
- deterministic issue sorting.

It contains no Research-domain identifiers beyond generic artifact labels and no urban-legend assumptions.

## Legacy reference namespace

`src/validation/` is retained as a reference implementation from the urban-legend project.

It is intentionally not deleted because it preserves useful implementation provenance for:

- cross-file reference checking;
- staged PASS / FAIL / ERROR handling;
- CLI orchestration;
- taxonomy validation patterns.

However, it contains lore-specific assumptions and is not authoritative for new Research behavior.

## Extraction rule

New Research code may copy or adapt a legacy algorithm only if its public contract no longer depends on:

- `Entry_ID`;
- four-digit lore entry paths;
- lore artifact suffixes;
- D01-D21 taxonomy;
- lore content / variant identifiers.

Task 08 builds Research-specific lineage validation on top of the generic core rather than modifying the legacy validator in place.
