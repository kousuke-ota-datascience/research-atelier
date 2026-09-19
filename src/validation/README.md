# Legacy validation reference implementation

This directory is retained as provenance from the earlier urban-legend workflow.

It is **not** the canonical implementation namespace for the general Research workflow.

Files here may contain lore-specific assumptions such as:

- four-digit `Entry_ID`;
- lore-specific artifact names and paths;
- D01-D21 taxonomy validation;
- variant/content identifiers from the urban-legend model.

The canonical Research validation implementation lives under:

`src/research_atelier/validation/`

Do not incrementally convert these legacy files into the Research implementation. Reuse design ideas or algorithms only after removing domain-specific assumptions.
