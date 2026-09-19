# Validation implementation boundary

## Canonical Research namespace

一般Research用validationのcanonical implementationは次とする。

`src/research_atelier/validation/`

generic coreは現在、以下を提供する。

- deterministic JSON parsing
- Draft 2020-12 JSON Schema validation
- stableなvalidation issue / result data structure
- deterministic issue sorting

generic artifact label以外のResearch-domain identifierや、都市伝説固有前提を含めない。

## Legacy reference namespace

`src/validation/` は旧・都市伝説projectのreference implementationとして保持する。

以下のimplementation provenanceを残すため、削除しない。

- cross-file reference check
- staged PASS / FAIL / ERROR handling
- CLI orchestration
- taxonomy validation pattern

ただしlore固有前提を含むため、新Research behaviorの正本ではない。

## Extraction rule

legacy algorithmを新Research codeへcopy / adaptしてよいのは、public contractが以下へ依存しなくなった場合だけとする。

- `Entry_ID`
- 4桁lore entry path
- lore-specific artifact suffix
- D01-D21 taxonomy
- lore content / variant identifier

Research-specific lineage validationはgeneric core上へ実装し、legacy validatorをin-place変換しない。
