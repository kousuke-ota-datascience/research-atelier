# Investigation identity / lifecycle / compatibility

## 目的

本書は、Research Question（RQ）、Investigation、Investigation Contextのidentity・cardinality・lifecycle、およびlegacy v1 artifactとの互換方針を定義する。

本書は `0001_research_architecture.md` に従う。mutableなRQ catalogはNotionが正本であり、1回のResearch executionをfreezeしたcanonical artifact chainはGitが正本である。

## 1. Canonical domain model

v2では次を採用する。

```text
Research Question (RQ)
  1
  |
  | 0..*
  v
Investigation (INV)
  |
  +-- 00_context = Investigation Context
  +-- 10_evidence
  +-- 20_synthesis
  +-- 30_analysis
```

### Research Question

RQは「何を問うか」という長期的semantic identityである。

canonical ID: `RQ-<NNNN>`

Regex: `^RQ-[0-9]{4}$`

RQ wordingの編集だけでidentityを変えない。回答集合、target construct、estimand等が実質的に変わる場合にだけ新RQを作る。

### Investigation

Investigationは、exactly one RQを特定のexecution conditionの下で1回実行する独立identityである。

v2 canonical ID: `INV-<NNNNNN>`

Regex: `^INV-(?!000000)[0-9]{6}$`

Investigation IDはRQ IDをencodeしない。RQとの対応はartifactの `rq_id` で明示する。

### Investigation Context

Investigation Contextは、そのInvestigationのexecution semanticsを規定するinput snapshotである。authorityは `00_context.json` に置く。

代表的な内容:
- frozen question wording
- Question Type
- Scope
- inclusion / exclusion
- evidence cutoff（必要な場合のみ）
- analytical / operational assumptions
- frozen timestamp
- Notion RQ provenance

`00_context` はResearch Context entityではない。

## 2. Research Contextをfirst-class entityにしない理由

Research Contextという語は、problem、decision context、hypothesis、domain framingなどRQより上流の文脈を指しうる。

しかし現時点で、Research Context自体をRQから独立してversioningすること、同一Context versionを複数Investigationからcanonical referenceすること、Context IDをlineage / validator / projectionの必須keyとすること、の実証要件はない。

first-class entity化するとResearch Context ↔ RQのN:M、Context Version ID、projection、migration、validatorが追加される一方、現行workflowの再現性要件はInvestigation Contextで満たせる。

したがってv2ではResearch Contextをcanonical identity modelへ入れない。将来、独立再利用・versioningの要件が確認された場合は別ADRで追加する。

## 3. Cardinality

- Research Question 1 : Investigation 0..*
- Investigation : Research Question = exactly 1
- Investigation : Investigation Context = exactly 1 canonical `00_context` after materialization

同じRQを異なるScope、cutoff、assumption、Evidence snapshotで再実行する場合、それぞれ別Investigationになる。

Research Context ↔ RQのcardinalityはv2 canonical contractの対象外である。

## 4. Draft / frozen / accepted lifecycle

### Draft

`00_context.context_state = draft` の間は、同じInvestigationをin-placeでrefineしてよい。unknownを埋めるために架空defaultを作ってはならない。

### Frozen

`context_state = frozen` かつ `frozen_at` が設定された時点でInvestigation Contextをfreezeする。

freeze後にcontext-defining fieldをsemanticに変更する場合、同じInvestigationを書き換えず **新しいInvestigation IDを採番する**。

### Accepted

current `30_analysis` をそのInvestigationのresultとしてacceptし、必要なprojectionが完了した状態。

accepted InvestigationのEvidence / Synthesis / Analysisをsubstantively再構成する場合も、新しいInvestigationを作る。

formatting、validator refactor、derived rendering再生成などcanonical research semanticsを変えない変更は新Investigationを要求しない。

## 5. RQ identity変更とInvestigation変更の境界

### 同じRQのまま新Investigation

- freeze後のScope変更
- freeze後のQuestion Type変更
- inclusion / exclusion変更
- evidence cutoff / time horizon変更
- analytical assumption変更
- dataset / source boundary変更
- accepted resultを新しいEvidence snapshotで再実行
- 同じ問いを別条件・別時点で再調査

### 新RQ

answer spaceまたは問いのsemantic targetが実質的に変わる場合は新RQを作る。

判断材料:
- target construct
- 問いに本質的なpopulation / unit of analysis
- causal treatment / comparator
- outcome / estimand
- prediction target
- central mechanism

単なるwording改善では新RQを作らない。

## 6. ID allocation

新規canonical Investigationはglobal sequenceとして `INV-NNNNNN` を採番する。

1. 既存 `INV-NNNNNN` の最大値を確認する。
2. 次の未使用整数を6桁0埋めで採番する。
3. 一度materialize / commitしたIDは再利用しない。
4. abandoned InvestigationのIDも再利用しない。
5. 同一RQのversion番号を意味するsuffixは持たない。

global sequenceはidentity allocationのためだけに使い、chronological quality rankingやsemantic versionを意味しない。

## 7. Cross-artifact identity invariant

1つのInvestigation directory内のcanonical artifactはすべて同じ `investigation_id` と同じ `rq_id` を持つ。

v2では `investigation_id` から `rq_id` を導出してはならない。

```text
investigations/
  INV-000001/
    00_context.json
    10_evidence.json
    20_synthesis.json
    30_analysis.json
```

## 8. Legacy v1 compatibility

既存 `RQ-NNNN-vVVV` はlegacy v1 Investigation IDとして保持する。

- historical directoryをv2 IDへrenameしない。
- historical JSONの `investigation_id` をrewriteしない。
- `schemas/v1` はlegacy contractとして凍結する。
- validatorはlegacy v1 IDとv2 IDの両方をvalidateできる。
- legacy v1ではID prefixと `rq_id` の一致を引き続き検査する。
- 新規Investigationにはlegacy形式を使わない。

## 9. Schema version

- legacy artifact: `schema_version = 1.0.0`, `schemas/v1`
- v2 canonical artifact: `schema_version = 2.0.0`, `schemas/v2`

v2の構造はv1を必要以上に変更しない。Task 17ではidentity semanticsとContext責務の修正に限定する。

`00_context.schema.json` のv2 title / documentationはInvestigation Contextであることを明示する。

## 10. Decision table

| Change | Draft Investigation | Frozen / Accepted Investigation | RQ identity |
| --- | --- | --- | --- |
| wordingの非意味的修正 | 同一INV | historical snapshot維持。必要なら新INV | 同一RQ |
| semantic question identity変更 | 新RQへ切替 | 新RQ + 新INV | 新RQ |
| Scope変更 | 同一INV | 新INV | 通常同一RQ |
| Question Type変更 | 同一INV | 新INV | 同一RQ |
| boundary / cutoff / assumption変更 | 同一INV | 新INV | 同一RQ |
| result accept前のEvidence更新 | 同一INV、downstream invalidate | N/A | 同一RQ |
| accepted resultのsubstantive再調査 | N/A | 新INV | 同一RQ |
| rendering / validator refactorのみ | 同一INV | 同一INV | 同一RQ |

## 11. Invariant

Investigation IDは、1つのRQに対して1つのfrozen Investigation Contextとartifact chainを束ねる独立Research execution identityである。

同じInvestigation IDが異なるRQ、異なるfrozen context、異なるaccepted executionを指してはならない。
