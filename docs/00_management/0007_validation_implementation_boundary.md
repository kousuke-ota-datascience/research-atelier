# Validation implementation boundary

## Canonical Research namespace

general Research validationのcanonical implementationは次に置く。

`src/research_atelier/validation/`

現在のgeneric coreは以下を提供する。

- deterministic JSON parsing
- Draft 2020-12 JSON Schema validation
- stableなvalidation issue / result data structure
- deterministicなissue sorting

generic artifact label以外のResearch-domain identifierを持たず、urban-legend固有前提も含めない。

## Legacy reference namespace

`src/validation/` はurban-legend project由来のreference implementationとして保持する。

削除しない理由は、以下の有用なimplementation provenanceを残すためである。

- cross-file reference checking
- staged PASS / FAIL / ERROR handling
- CLI orchestration
- taxonomy validation pattern

ただしlore-specificな前提を含むため、新Research behaviorのauthorityにはしない。

## Extraction rule

新Research codeがlegacy algorithmをcopy / adaptしてよいのは、public contractから以下の依存を除去した場合のみである。

- `Entry_ID`
- 4桁lore entry path
- lore artifact suffix
- D01-D21 taxonomy
- lore content / variant identifier

Task 08ではlegacy validatorをin-placeで改造せず、このgeneric core上にResearch-specific lineage validationを構築する。
