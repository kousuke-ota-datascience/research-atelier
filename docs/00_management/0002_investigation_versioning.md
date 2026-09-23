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

Investigation Contextは、そのInvestigationのexecution semanticsを規定するinput snapshotである。**freeze前のmutable operational input authorityはNotion Investigations DB、freeze後のcanonical authorityは `00_context.json`** とする。

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

### Notion operational representation

Notionの `Investigations` DBはcanonical Investigation domain entityのoperational registryであり、**1 Investigation = 1 row** とする。別のdomain identityを追加するものではない。

- title propertyはcanonical `Investigation ID` をそのまま保持する。
- `Research Question` relationでexactly one RQへexplicitにbindする。v2ではInvestigation IDからRQを推定しない。
- freeze前のQuestion Type / Scope / Include / Exclude / Evidence Cutoff / Assumptionsはこのrowでrefineする。
- Question wordingはrowへduplicateせず、Research Questions DBをcurrent semantic authorityとしてfreeze時にsnapshotする。
- Review Status / Latest Review SeqはReviewのcurrent operational pointerであり、Review historyやFinding/Verdictのcanonical storeではない。

new InvestigationではWorkflow 00がID採番直後、`00_context` freeze前にrowを1件作成する。resumeではInvestigation IDで既存rowをreuseし、duplicate rowを作らない。同じIDのrowが複数ある場合はfail-stopする。

ID採番とrow作成はdraft workspace確保であり、Context freezeやsubstantive research execution開始を意味しない。Question Type未確定のままID/rowが存在しても、同じdraft INVをBLOCKEDとして保持し、Human commitment後に同じINVでfreezeへ進む。Question Type確定だけを理由に再採番しない。

既存Git Investigationにrowがない場合は、frozen `00_context` をauthorityとしてrowをbackfillしてよい。historical Scope等をcurrent RQ metadataから逆算しない。

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

freeze前はNotion Investigations rowがmutable Investigation Context inputのauthorityである。同じInvestigationをin-placeでrefineしてよい。unknownを埋めるために架空defaultを作ってはならない。

Question Typeはdraftではnullを許容する。ただしnullの間はWorkflow 00 / 10をBLOCKEDとし、new frozen Contextや `10_evidence` を成立させない。draft内の `null -> concrete Question Type` はversion changeではなくsemantic prerequisiteの確定であり、同一INVのまま扱う。

一時的に `00_context.context_state = draft` をmaterializeしてよいが、freeze完了まではcandidate representationであり、Notion rowと独立したcanonical authorityにはしない。

### Frozen

新規v2 freezeでは、`context_state = frozen`、`frozen_at` 設定に加え、`question_type != null` をoperation-time invariantとする。通常のv2 JSON Schemaはhistorical compatibilityのためnullを許容し続け、新規freeze可否は `validate_investigation --through 00 --new-freeze` で判定する。

`context_state = frozen` かつ `frozen_at` が設定され、new-freeze validation後に `00_context.json` がcommitされた時点でInvestigation Contextをfreezeする。以後、そのInvestigation Contextのcanonical authorityはGit `00_context` である。

Notion rowはoperational / derived representationとして残すが、frozen contextと不一致ならGitを基準にreconcileし、Notion側の編集からhistorical Git artifactを変更しない。

freeze後にcontext-defining fieldをsemanticに変更する場合、同じInvestigationを書き換えず **新しいInvestigation IDを採番する**。具体的Question Typeの `Descriptive -> Mechanistic` 等は従来どおりnew Investigationである。

BKL-0031以前に存在するfrozen `question_type = null` artifactはhistorical compatibility対象であり、Question Typeをbackfillしてcurrent Contextへrepairしない。regular schema validationで一律INVALID化せず、missing downstream artifactも後付けしない。

### Accepted

current `30_analysis` をそのInvestigationのresultとしてacceptし、必要なprojectionが完了した状態。

accepted Investigationでも、**frozen Investigation Contextと独立execution intentが不変なら、Review Findingやoperational defectを解消するためのsame-Investigation repairを許容する**。acceptedという事実だけでnew Investigationへ分岐しない。

same-Investigation repairに含める:
- Contextですでに要求していたEvidence selection omissionの補完
- 同一dataset / source boundary内のEvidence取りこぼし修正
- Evidence -> Synthesis lineage / relation修正
- Evidence support boundaryを超えたAnalysis表現の修正
- 上記repairに伴う20_synthesis / 30_analysisのdownstream rebuild
- projection / validation / connector / reconciliation retry
- formatting、validator refactor、derived rendering再生成等、canonical research semanticsを変えない変更

new Investigationが必要なのは、freeze済みContext-defining conditionを実質的に変える場合、Evidence population / snapshotの意味を変える場合、またはHumanが既存結果とは独立した別executionを明示した場合である。

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

新規canonical Investigationはglobal sequenceとして `INV-NNNNNN` を採番する。ただし、**採番の前に既存Investigationとのsemantic-equivalence guardを必ず通す**。

Humanの「再度実行」「やり直し」「retry」「もう一度」等の自然言語だけをnew allocation triggerにしない。Workflow 00は今回のintentを最低限次のいずれかへ分類する。

- `retry_completion`
- `repair`
- `explicit_new_execution`
- `semantic_reinvestigation`

比較対象は少なくともResearch Question、Question Type、Scope、Include / Exclude、Assumptions、Evidence cutoff / time horizon、dataset / source boundaryとする。requested inputが既存fieldを再提示していない場合、その欠落自体をsemantic differenceと解釈しない。

Evidence cutoffの値だけが異なる場合、timestamp差だけではnew Investigationを正当化しない。Evidence population / snapshotの意味が変わったかを別に解決し、未解決なら採番せずBLOCKEDとする。

canonical deterministic helperは `src/research_atelier/orchestration/investigation_allocation.py` とする。decisionは `reuse_existing / allocate_new / blocked` のいずれかで、少なくとも次をmachine-readableに残す。

- `decision`
- `selected_existing_investigation`
- `new_investigation_allocated`
- `semantic_differences`
- `explicit_new_execution_intent`

new INVを採番した場合、既存INVをresume / repairできなかった理由を `reason_codes` とsemantic differenceで追跡可能にする。

1. semantic-equivalence guardが `allocate_new` を返したことを確認する。
2. 既存 `INV-NNNNNN` の最大値を確認する。
3. 次の未使用整数を6桁0埋めで採番する。
4. 一度materialize / commitしたIDは再利用しない。
5. abandoned InvestigationのIDも再利用しない。
6. 同一RQのversion番号を意味するsuffixは持たない。
7. draft rowでQuestion Type等のsemantic prerequisiteを確定する間は同じIDを保持し、未確定値のcommitだけを理由にnext IDをallocateしない。

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
- Notion Investigations DBへbackfillする場合もlegacy IDをそのままrow titleとして使い、new v2 IDへ置換しない。
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
| Question Type `null -> concrete` | 同一INV（draft prerequisite確定） | historical null frozen artifactはin-place repairせず保存 | 同一RQ |
| concrete Question Type変更 | 同一INV（freeze前） | 新INV | 同一RQ |
| boundary / cutoff / assumption変更 | 同一INV | 新INV | 同一RQ |
| result accept前のEvidence更新 | 同一INV、downstream invalidate | N/A | 同一RQ |
| Review FindingによるEvidence / Synthesis / Analysis repair（frozen Context不変） | 同一INV | 同一INV | 同一RQ |
| accepted resultを別Evidence snapshot / 別時点の独立executionとして再調査 | N/A | 新INV | 同一RQ |
| rendering / validator / projection / connector repairのみ | 同一INV | 同一INV | 同一RQ |

## 11. Invariant

Investigation IDは、1つのRQに対して1つのfrozen Investigation Contextとartifact chainを束ねる独立Research execution identityである。

同じInvestigation IDが異なるRQ、異なるfrozen context、異なるaccepted executionを指してはならない。
