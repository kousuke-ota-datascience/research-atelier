# Research architecture / authority boundary

## 目的

本書は、research-atelier における責務と authority boundary の正本仕様である。

同じ情報を複数箇所で独立管理しないため、capture、frozen research artifact、意味論的構築、構造契約、deterministic enforcement を分離する。

## 文書言語

正本ドキュメントの基本言語は日本語とする。

ただし、以下は理解・契約上の明確性を優先し、必要に応じて原語のまま使用する。

- JSON field名
- path / CLI / identifier
- JSON Schema用語
- Research Question / Investigation / Working Answer / Question Type / lineage など、英語のままの方が参照関係を保ちやすい技術用語
- 規格・ライブラリ・製品・固有名詞

## Authority model

| 対象 | System / artifact | 責務 | Authority |
| --- | --- | --- | --- |
| Discovery、capture、reusable catalog、運用上のcurrent state | Notion | Research Topics、Research Questions、Sources、Evidence Notes、task state、運用metadata | mutableな運用状態とreusable catalog recordの正本 |
| Frozen Investigation artifact | Git JSON | Investigation Context、Evidence snapshot、Synthesis、Analysis | 特定Investigationの正本 |
| 意味論的構築・判断 | LLM | structured Synthesis、分析判断、mapping案の作成 | 単独では正本ではない。指定canonical artifactへmaterializeされ、必要なvalidation/reviewを通過して初めて正本化される |
| 構造契約 | JSON Schema | 許可構造、required、type、enum、conditional structure | artifact structureの正本契約 |
| Deterministic enforcement | Python | schema、reference、ID、version/path、その他機械判定可能なinvariantの検査 | machine-checkable ruleの実行正本 |

## Domain identity model

v2のcanonical domain modelは次のとおり。

```text
Research Question (RQ)
  1
  |
  | 0..*
  v
Investigation (INV)
  |
  +-- 00_context = frozen Investigation Context
  +-- 10_evidence
  +-- 20_synthesis
  +-- 30_analysis
```

- **Research Question** は「何を問うか」の長期的semantic identityであり、Notion catalogがcurrent stateの正本である。
- **Investigation** は、1つのRQを特定のexecution conditionで実行する独立identityである。v2のIDは `INV-NNNNNN` とし、RQ IDをID文字列へ埋め込まない。
- **Investigation Context** はInvestigation固有のimmutable execution inputであり、`00_context.json` がfreeze後の正本である。
- **Research Context** はproblem / decision context / hypothesis / domain framing等の上流概念を指す一般語としてのみ使用する。v2では独立identity、独立version、canonical DBを持つfirst-class entityにはしない。
- 将来、同一framingを複数RQ / Investigationから独立に再利用・versioningする実需要が確認された場合に限り、Research Contextを別entityとして追加する。その場合もInvestigation Contextと混同しない。

canonicalに固定するcardinalityは **RQ 1 : Investigation 0..*** であり、各Investigationはexactly one RQを参照する。

## Single-authority rule

各情報クラスは、必ず1つだけcanonical authorityを持つ。

derived copyはprojection、snapshot、cache、renderingとしてのみ存在できる。derived representationを独立編集可能な第二の正本にしてはならない。

表現同士が矛盾した場合は、本書で定義したcanonical authorityを優先する。非正本側は再生成・reconcile・invalidateする。

## 情報クラス別の正本

### Notion-authoritative

- Research Topic catalogとmutable metadata
- Research Question catalogとmutable operational metadata
- Source identityとbibliographic metadata
- source-faithfulなreusable Evidence Note
- Backlog / workflow statusなどのoperational current state

### Git artifact-authoritative

1つのfrozen Investigationについて:

- Investigation Context
- そのversionで選択したEvidence snapshot
- evidence-faithful Synthesis
- RQ-specific AnalysisとWorking Answer
- canonical artifact内のlineage / version identifiers

### Contract-authoritative

- JSON Schemaはartifact shapeの正本である。
- JSON Schemaだけでは表現しにくいcross-artifact constraintはPython validationを正本実装とする。

### 非正本のcomputational actor

- LLM outputは、canonical artifactへ書き込まれvalidationされるまではsemantic proposalである。
- rendered document、summary、dashboard、NotionへのGit結果projectionは、別仕様で昇格されない限りderived viewである。

## Write-direction constraints

1. Notion catalog dataは、frozen Git Investigation artifactへsnapshotしてよい。
2. Git canonical analysisはNotionのoperational current stateへprojectionしてよいが、別のsync contractがauthority transferを明示しない限りderivedである。
3. projectionにはsource Investigation identityを識別できるprovenanceを残す。
4. 同一fieldをNotionとGitの双方でauthoritativeに手動管理してはならない。
5. upstream canonical artifactが変更された場合、依存するdownstream artifactは再validationまたは再生成されるまでinvalidとする。

## docs/98_reusable_artifact の位置付け

`docs/98_reusable_artifact` は、旧・都市伝説workflowから継承したreference / provenance materialである。

設計参照として保持するが、新Research workflowの正本仕様ではない。

新Research仕様は主として `docs/00_management`、`docs/10_workflows`、Research用schema / implementationへ置く。

## 設計上の帰結

Research workflowは次の分離を基本とする。

`Evidence -> evidence-faithful structured representation -> analytical judgment`

実装責務は次のとおり。

```text
Notion       = operational state / reusable catalog
Git JSON     = frozen canonical artifact
LLM          = semantic construction / judgment
JSON Schema  = structure contract
Python       = deterministic enforcement
```

このboundaryを、Investigation identity/lifecycle、canonical artifact、validation、Notion/Git projectionの前提とする。
