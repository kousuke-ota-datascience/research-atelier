# Legacy validation reference implementation

このdirectoryは、旧urban-legend workflow由来のimplementation provenanceを保持するために残す。

一般Research workflowにおけるcanonical implementation namespaceではない。

このdirectory内のfileには、たとえば以下のlore-specific assumptionが含まれ得る。

- 4桁の `Entry_ID`
- lore-specific artifact name / path
- D01-D21 taxonomy validation
- urban-legend model固有のvariant / content identifier

canonical Research validation implementationは次に置く。

`src/research_atelier/validation/`

legacy fileを段階的に改造してResearch implementationへ変換してはならない。

design ideaやalgorithmを再利用する場合は、domain-specific assumptionを除去したうえでcanonical Research namespaceへ抽出する。
