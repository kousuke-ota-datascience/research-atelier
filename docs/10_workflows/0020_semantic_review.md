# Workflow 20 — Independent Semantic Review

## 0. 位置付け

Workflow 20は、1つのInvestigationについて、deterministic validationでは判定できない**research-semantic correctness**を独立に評価するoptional workflowである。

canonical domain modelは変更しない。

```text
Research Question
  1
  └─ 0..* Investigation
           ├─ 00_context = Investigation Context
           ├─ 10_evidence
           ├─ 20_synthesis
           └─ 30_analysis
```

- primary review identityは **Investigation** である。
- Research Questionはsemantic parent identityであり、Review identityではない。
- `00_context` は **Investigation Context** であり、Research Context entityではない。
- Workflow 20はResearch Questionを再定義・採択しない。
- Workflow 20はWorkflow 10のartifact constructionやdeterministic validationを再実装しない。
- Workflow 20はControl Planeの同期・reconciliationを担わない。

BKL-0021時点ではWorkflow 20を**optional**とする。Workflow 00の通常の `VALIDATED / COMPLETE` contractにReview gateを追加しない。

## 1. Public input

通常のpublic inputは1件の `Investigation_ID` とする。

v2例:

```text
INV-000001
```

Workflow 20はこのIDからcanonical artifactを解決し、artifact内の `rq_id` からResearch Question bindingを確認し、`00_context` からfrozen Investigation Contextを読む。

通常inputとして以下を要求しない。

- Research QuestionをReview identityとして指定すること
- Investigation Contextを別identityとして指定すること
- internal artifact path
- validator stage
- Review Seq

RQ IDだけが与えられた場合、どのInvestigationをReviewするかを推測してはならない。対象Investigationが一意に指定されるまでBLOCKEDとする。

## 2. 実行契機

Workflow 20を開始してよいのは次のいずれかの場合とする。

1. Human / Researcherが特定InvestigationのSemantic Reviewを明示的に要求した。
2. Workflow 00が、明示された運用方針またはhigh-risk use等の理由により、そのInvestigationへoptional Reviewを要求した。

Workflow 10がthrough-30 PASSへ到達したこと自体はWorkflow 20の暗黙起動条件ではない。

Reviewを実行しなかったことだけを理由に、Workflow 00の通常のCOMPLETE判定を失敗させない。

## 3. Review開始条件

最低条件:

- `00_context / 10_evidence / 20_synthesis / 30_analysis` が存在する。
- frozen `00_context.question_type` がnon-nullである。
- Review対象chainがcurrent deterministic contract上でvalidと扱える。
- canonical artifactがGitへcommitされている。
- Review対象版を一意に固定できる。

### Historical null Question Type compatibility

BKL-0031以前にfreezeされたhistorical Investigationのうち、`00_context.question_type = null` のものはWorkflow 20の**Review非対象**とする。

- Review cycleを開始しない。
- Review Seqをallocateしない。
- Review JSONを生成しない。
- Notion Investigations DBは `Review Status = －（対象外）`、`Latest Review Seq = empty` へreconcileする。
- HumanがReviewを明示要求してもeligibility ruleを上書きしない。
- historical `00_context` へQuestion Typeをbackfillしない。
- missing `30_analysis` をReviewのために後付けしない。

これはhistorical compatibility ruleであり、新規Investigationで `question_type = null` のfreezeを許容する根拠ではない。BKL-0031以後のnew freezeは `validate_investigation <ID> --through 00 --new-freeze` により `question_type != null` をoperation-time invariantとして強制する。通常のv2 schema validationはhistorical互換のためnullを許容し続ける。

### Validation freshness

Workflow 20開始のたびに `validate_investigation <ID> --through 30` を**機械的に再実行することは要求しない**。

再実行不要の典型例:

- Workflow 10 / Workflow 00で既にthrough-30 PASSとして成立したcurrent targetを、そのartifactを変更せずReviewする。
- Review開始後も対象artifactに変更がなく、applicable schema / validator contractにもReview可否を左右するknown changeがない。
- BKL-0021のようにworkflow contractだけを変更し、review対象Investigation artifact自体は変更していない。

再validationが必要な条件:

1. review target artifactが変更された。
2. upstream changeによりdownstream invalidationが発生した、またはその疑いがある。
3. applicable JSON Schema / Research-specific validator contractが変更され、旧PASSをcurrent validityの根拠として扱えない。
4. targetのdeterministic validityが不明・矛盾・疑義ありである。
5. repair後のnew targetをreReviewする。

deterministic validationが既知のFAIL / ERRORである場合、Semantic Reviewで補完してPass扱いにしない。先にWorkflow 10 / validator boundaryで修復する。

したがって、Workflow 20のpreconditionは「**Review開始時に毎回CLIを叩くこと**」ではなく、「**semantic Review対象がdeterministically validなcanonical chainであること**」である。

## 4. Review target freeze

Review開始時は `src/research_atelier/reviewing/review_writer.py::prepare_review_cycle()` と同じcontractでtargetをfreezeする。

固定するもの:

- `investigation_id`
- next per-Investigation `review_seq`
- reviewed canonical chainを含むGit commit SHA
- `00_context / 10_evidence / 20_synthesis / 30_analysis` の各blob SHA

Review cycle identityは `(Investigation ID, Review Seq)` とする。global `REV-NNNN` は導入しない。

prepare時に既存Review historyがmalformed、Schema invalid、Seq欠番、filename / payload不一致ならfail-stopする。Review中にtargetを読み替えない。

save直前にcommit SHAと4 artifact blob SHAを再取得し、prepare時snapshotとexact一致しなければ保存しない。new targetを再prepareして別cycleとしてReviewする。

### Staleness rule

次の場合、old Review outcomeをcurrent artifactへ流用しない。

- frozen artifact blobのいずれかが変わった。
- upstream artifact変更によりreviewed downstreamがinvalidatedされた。
- repairによりnew targetが成立した。
- repair directionが `new_investigation` でnew Investigationへhandoffされた。

Review target commit SHAはaudit provenanceとして保持する。canonical chainのcontent stalenessはartifact blob SHAを主に用い、別fileだけのcommit差分をsemantic target changeと誤認しない。

Git ancestryからReview targetがcurrent artifactよりahead / divergedと判定される場合は自動収束せずBLOCKEDとする。SHA relationのmechanical判定はadapter / Control Plane責務でありReviewerのsemantic judgmentにしない。

## 5. Reviewするsemantic layer

Reviewはcanonical chainの順序を維持し、new split-format cycleでは4 layerを独立assessmentとして記録する。

### 5.1 `00_context` semantic validity

確認対象:

- frozen Research Question / Scope / assumptionsとInvestigation Contextの整合。
- Question Typeとcontext設計の意味論的一貫性。
- downstream Analysisの解釈に必要なscope / population / temporal boundary / assumptions等の欠落。
- context内部のsemantic contradiction。
- frozen contextを変更しなければ修正できないdefect。

freeze済み `00_context` のsubstantive defectは原則 `repair_direction.mode = new_investigation` とする。same-Investigation repairはunsafeとしてfail-stopする。

### 5.2 Source / Evidence Note provenance -> `10_evidence`

確認対象:

- Evidence contentがSourceへtraceでき、source-faithfulか。
- quote / paraphrase / locator / provenanceが意味論上妥当か。
- selectionによって重要な反証・qualification・uncertaintyが不当に落ちていないか。
- Notion Evidence Noteとfrozen Evidence snapshotの意味が変質していないか。

Source上の情報を直接Analysisへ持ち込んで不足を補完しない。Evidence layerの不足はupstream findingとして扱う。

### 5.3 `10_evidence` -> `20_synthesis`

確認対象:

- knowledge unitが参照Evidenceでsupportされるか。
- unsupported propositionや過剰一般化がないか。
- disagreement / conflict / uncertainty / qualificationが消失していないか。
- cross-source synthesisとSource自身のclaimが区別されているか。
- downstream Analysisに必要なmeaningを作るためEvidenceを越えていないか。

### 5.4 `20_synthesis + 00_context` -> `30_analysis`

確認対象:

- frozen RQ / Scope / assumptionsに対するRQ-specific inferenceになっているか。
- `question_type` 固有のmethodological validityを満たすか。
- Judgment / Working AnswerがSynthesisを越えて断定していないか。
- limitation / alternative explanation / unresolved questionが重要な不確実性を保持しているか。
- raw Evidence / Sourceを直接使って `20_synthesis` をbypassしていないか。

layer verdictは「そのreview layerでFindingが存在するか」を表す。Findingの `repair_direction.affected_layer` は「repair開始layer」を表し、両者を混同しない。cross-layer defectの場合、発見元layerとaffected layerが異なってよい。

## 6. No-bypass / no-upstream-healing rule

Reviewでもcanonical no-bypass ruleを維持する。

- Source / Evidenceから直接 `30_analysis` を正当化しない。
- Review 20相当のdownstream監査が、upstream omissionを直接補完してPassへ戻さない。
- upstream findingがある場合、canonical layerをrepairし、そのdownstreamをinvalidation ruleに従って再構築・再評価する。

Reviewはcanonical chainの外側から結論を補強する第二のanalysis pipelineではない。

## 7. Deterministic validationとの境界

Workflow 20が再実装しないもの:

- JSON Schema validity
- required field
- ID format / uniqueness
- cross-reference existence
- lineage reference existence
- schema version / path consistency
- deterministic projection state

これらは `src/research_atelier/validation/` のResearch-specific validatorまたは既存deterministic componentへ委譲する。

`src/validation/` のurban-legend legacy implementationをgeneral Research behaviorのauthorityにしない。

## 8. Finding contract

Semantic findingを記録する場合、最低限次を持つ。

- **target**: 対象artifact、section / item ID、またはsemantic transition
- **evidence**: findingの根拠となるcanonical artifact reference / Source provenance
- **impact**: 放置した場合にWorking Answer・lineage・methodological validityへ与える影響
- **repair_direction**: どのcanonical layerをどの方向で修正すべきか
- **severity**: `Minor / Moderate / Major`

severityの目安:

- `Minor`: main conclusionを直ちに反転させないが、表現・qualification・traceabilityの修正が必要。
- `Moderate`: Working Answerまたは重要judgmentのsupport境界・方法論的妥当性に影響する。
- `Major`: main conclusionまたは核心的lineageをtrustできない。

Reviewerはfindingを記録する。canonical artifactをReviewの名義で直接修正しない。

## 9. Canonical Review result / outcome

Workflow 20を実行した場合、Review結果をephemeral chat outputで終わらせない。canonical authorityはGit上のmachine-readable JSONとする。

### 9.1 New split-format cycle

BKL-0034以降の新規Review Cycleは次の5 fileで保存する。

```text
investigations/<Investigation ID>/reviews/
  review-000002.json
  review_00_000002.json
  review_10_000002.json
  review_20_000002.json
  review_30_000002.json
```

- `review-XXXXXX.json`: cycle manifest。Review identity、target commit / 4 artifact blob SHA、reviewed_at、layer file references、overall verdict。
- `review_00_XXXXXX.json`: `00_context` semantic assessment。
- `review_10_XXXXXX.json`: Source / Evidence Note -> `10_evidence` assessment。
- `review_20_XXXXXX.json`: `10_evidence` -> `20_synthesis` assessment。
- `review_30_XXXXXX.json`: `20_synthesis + 00_context` -> `30_analysis` assessment。

canonical schema:

- `schemas/v2/review_manifest.schema.json`
- `schemas/v2/review_00_context.schema.json`
- `schemas/v2/review_10_evidence.schema.json`
- `schemas/v2/review_20_synthesis.schema.json`
- `schemas/v2/review_30_analysis.schema.json`
- common definitions: `schemas/v2/review_layer_common.schema.json`

Review Cycle identityは `(Investigation ID, Review Seq)` とする。global `REV-NNNN` は導入しない。

Finding IDはcycle-global `F001...` とし、logical identityは `(Investigation ID, Review Seq, Finding ID)` で表す。

layer-level Verdictとcycle-level VerdictはReviewerが独立入力しない。

- layer Finding 0件 -> layer `PASS`
- layer Finding 1件以上 -> layer `FINDINGS`
- 4 layer全体でFinding 0件 -> cycle `PASS`
- 4 layer全体でFinding 1件以上 -> cycle `FINDINGS`

`STALE / BLOCKED` はcanonical semantic Verdictではなく、target relation / execution conditionからreconcilerが導出するworkflow outcomeである。

### 9.2 Legacy compatibility

> **DEPRECATED SCHEMA WARNING**
>
> `schemas/v2/review_cycle.schema.json` と `schemas/v2/review_common.schema.json` はhistorical compatibility専用であり、**新規Workflow 20 Reviewのauthoringに使用してはならない**。
>
> legacy実体は `schemas/v2/legacy/` 配下に置く。top-level旧pathは既存参照を壊さないためのdeprecated compatibility redirectである。
>
> Human researcher / LLM executorは、新規Reviewを作成するときに旧2 schemaを選択候補から除外する。

BKL-0034以前のsingle-file canonical Review Cycleはhistorical factとして保持し、in-place rewriteしない。

```text
review-000001.json
report_type = semantic_review
```

deprecated compatibility path `schemas/v2/review_cycle.schema.json`（実体: `schemas/v2/legacy/review_cycle.schema.json`）をhistorical validatorとして維持する。history loaderはlegacy single-file cycleとnew split cycleの双方をnormalized Review Cycleへ変換し、projection / reconciliationへstorage format差を漏らさない。

new split cycleでmanifestまたは4 layer fileの一部欠落、orphan layer、filename / payload Seq不一致、target SHA不一致、duplicate Finding ID、Verdict / Finding mismatchがある場合はfail-stopする。

Markdown Reviewは作成してもderived viewであり、Review history / completion / reconciliationの事実源にしない。

### 9.3 Workflow execution schema guard

新規Review Cycleを開始する前に、executorはschema selectionを確認する。

```text
CURRENT / use for new Review:
  schemas/v2/review_layer_common.schema.json
  schemas/v2/review_manifest.schema.json
  schemas/v2/review_00_context.schema.json
  schemas/v2/review_10_evidence.schema.json
  schemas/v2/review_20_synthesis.schema.json
  schemas/v2/review_30_analysis.schema.json

DEPRECATED / historical validation only:
  schemas/v2/review_common.schema.json
  schemas/v2/review_cycle.schema.json
  schemas/v2/legacy/*
```

new Review writer / reviewer instructionがdeprecated schemaを新規authoring schemaとして指定している場合、そのinstructionをstale contractとして扱い、current split schema setへ読み替える。historical Review validationの場合だけdeprecated schemaを使用する。

## 10. Repair handoff

Reviewerとrepair executorの責務を分離する。

findingのrepair開始位置:

| Finding target | Repair start | Downstream handling |
| --- | --- | --- |
| `00_context` semantic condition | versioning contractに従い、freeze後のContext-defining changeならnew Investigation | successor INVで10/20/30を構築 |
| Source / Evidence / `10_evidence` | Workflow 10 Evidence stage。frozen Context不変ならsame Investigation | 20 / 30をinvalidate |
| `20_synthesis` | Workflow 10 Synthesis stage。frozen Context不変ならsame Investigation | 30をinvalidate |
| `30_analysis` のみ | Workflow 10 Analysis stage。frozen Context不変ならsame Investigation | 30をrepair / revalidate |

accepted Investigationであること自体はnew Investigation triggerではない。Review Findingが、既存Contextで要求済みのEvidence selection omission、同一source boundary内の取りこぼし、Evidence -> Synthesis lineage誤り、Evidence support boundaryを超えたAnalysis表現、またはそのdownstream rebuildで解消できる場合はsame-Investigation repairとする。

Workflow 20の `repair_direction.mode` はversioning contractを迂回して独立executionを新設する権限ではない。Workflow 00はrepair handoff時に `src/research_atelier/orchestration/investigation_allocation.py` のallocation guardを適用し、Context-defining semantic differenceまたはHumanのexplicit independent execution intentがある場合だけnew Investigationへhandoffする。

### Valid new-Investigation handoff completion

`repair_direction.mode = new_investigation` はhandoff requestであってhandoff completionではない。旧InvestigationのReview lifecycleをterminalへ移すには、次をすべて満たす。

1. source latest ReviewのVerdictが `FINDINGS` で、少なくとも1 Findingが `new_investigation` を要求している。
2. BKL-0035 allocation guardのmachine-readable decisionが `allocate_new` で、source Investigationを明示している。
3. successor Investigationがpersist済みである。
4. successorがsourceのexpected RQへexactly one relationでbindされている。
5. source Reviewの全Findingをsuccessorへhandoffするprovenanceがappend-onlyで保存されている。

canonical handoff artifact:

```text
investigations/<source Investigation ID>/reviews/
  handoff-<Review Seq>.json
```

schema / implementation:

- `schemas/v2/review_handoff.schema.json`
- `src/research_atelier/reviewing/handoff.py`

最低限のprovenanceは `source_investigation_id / source_review_seq / source_rq_id / finding_ids / handoff_mode / successor_investigation_id / successor_rq_binding / versioning_decision / handoff_at` を持つ。Review manifest / layer JSONへhandoff結果を追記せず、source ReviewのVerdictは `FINDINGS` のままimmutableに保つ。

handoff artifactを保存・再読込・validationした後にだけWorkflow 00は `new_investigation_handoff_completed` eventをreconcilerへ渡す。これによりsource Investigationの `Review Status` は `要修正 -> 引継済` へ遷移する。`引継済` は「Review PASS」ではなく「FINDINGSのrepair responsibilityをvalid successorへ移譲済み」を意味する。allocation / persistence / RQ binding / provenance validationが失敗した場合はterminalへ遷移しない。

rerunでは**allocationより先に** `preflight_review_handoff()` を実行する。expected canonical pathにvalid handoff artifactが既にあればrecord済み `successor_investigation_id` をreuseし、新しいsuccessorのallocation / ID採番も、新しいhandoff record作成も行わない。既存recordとsource Review / source RQが矛盾する場合は推測で上書きせずBLOCKEDとする。

repair後は新しいtarget SHA / blobをfreezeし、old Review outcomeを流用せずreReviewする。same-Investigation repair pathは従来どおり `要修正 -> 再作業中 -> 再レビュー待` を使い、本handoff terminal stateを使用しない。

## 11. Workflow 00 / 10との関係

### Workflow 10

Workflow 10のcompletion conditionはartifact construction + through-30 deterministic validationである。

Workflow 20はWorkflow 10 completionの必須条件ではなく、Workflow 10から暗黙起動しない。

### Workflow 00

defaultではReview未実施でも既存の `VALIDATED / COMPLETE` state contractを維持する。

ただし、Human / Workflow 00が**そのacceptance前にWorkflow 20実行を明示的 prerequisiteとして要求した場合**、そのReviewが完了するまでfinal acceptance / projectionへ進めない。

また、Review実施後にcurrent accepted resultへconfirmed findingが見つかった場合、そのfindingを無視して「既知のsemantic defectなし」と扱ってはならない。repair / new Investigationの要否をversioning / invalidation contractに従って決定する。

Reviewをmandatory state gateへ昇格する場合は、Task 14のdecisionを別途supersede / amendし、Workflow 00のstate modelを明示的に変更する。

## 12. Semantic ReviewとControl Planeの責務分離

### Semantic Review

担う:

- Evidence-faithfulness
- Synthesisのsupport / conflict / uncertainty preservation
- Question Type固有analysisの方法論的妥当性
- Working Answer / judgmentのsupport境界
- limitation / alternative explanation
- finding記述

担わない:

- SHA ancestry計算
- Git / Notion reconciliation
- projection current/staleの機械判定
- concurrent edit detection
- sync state tracking

### Control Plane

担う:

- canonical artifact version identification
- targetとcurrent artifactのmechanical staleness判定
- projection / sync state tracking
- divergence / concurrent editのdeterministic detection
- frozen `00_context` をReview reconcilerへ渡し、`derive_review_eligibility()` でQuestion Typeからeligibilityをdeterministically導出すること
- eligibility Contextが欠落・未freezeならeligible=trueへdefaultせずBLOCKEDとすること

担わない:

- research conclusionのsemantic judgment
- Evidence qualityの専門判断

## 13. Persistent Review implementation / BKL-0021 amendment

BKL-0021でdeferしていたpersistent Review infrastructureは、BKL-0027で次の範囲を採用する。

### 採用

- per-Investigation Review Seq
- append-only Review JSON
- split Review manifest / 4 layer / current common JSON Schema
- deterministic Review writer
- read-only Review history loader
- target commit / blob freeze
- prepare後target変更fail-stop
- deterministic Verdict aggregation
- Investigation rowの `Review Status / Latest Review` と `Latest Review Seq` compatibility pointer
- Notion `Reviews` DBへのhuman-facing operational projection
- Python reconcilerによるcurrent state mutation plan

canonical implementation:

- `src/research_atelier/reviewing/review_writer.py`
- `src/research_atelier/reviewing/review_state.py`
- `src/research_atelier/reviewing/reconcile.py`

### 引き続き採用しない / defer

- global first-class `REV-NNNN` identity
- Reviewをcore first-class domain entity / canonical authorityとするNotion DB
- artifactごとのNotion Status row
- Notion上のpre-SHA / post-SHA / target SHA property
- Markdown Reviewをcanonical authorityとすること
- persistent `レビュー中` Status
- `要再調査` Status

Workflow 20は引き続きoptionalであり、通常のWorkflow 10 completionをmandatory Review gateへ変更しない。ただしWorkflow 20を実行した場合、そのReview persistence / history / state reconciliationはmandatoryである。

## 14. Invariant

Workflow 20は**Investigationに対する独立semantic assessment**であり、Research Questionの意味を所有せず、canonical artifact chainを迂回せず、deterministic validatorやControl Planeを再実装せず、findingとrepair executionを混同しない。


## 15. Notion Reviews operational projection / BKL-0032

BKL-0032では、BKL-0027でdeferしていた**human-facing Review DB**をoperational projectionとして導入する。ただしReview cycleのdomain positionとauthorityは変更しない。

- Review cycleはInvestigationに従属するpersistent assessment recordであり、独立したcore domain entityではない。
- logical identityは引き続き `(Investigation ID, Review Seq)` とする。global `REV-NNNN` は導入しない。
- canonical authorityはGit `review-XXXXXX.json` のままである。
- Notion `Reviews` DBはGit canonical Review JSONからdeterministically生成・更新するderived operational surfaceである。
- Notion上のhuman editをGit canonical Review JSONへreverse applyしない。

### Reviews DB projection

1 canonical Review cycleにつき1 rowをprojectionする。

主要property:

- `Review`: `<Investigation ID> / Review <6桁Seq>`
- `Investigation`: Investigations DB relation
- `Review Seq`
- `Verdict = PASS / FINDINGS`
- `00 Context / 10 Evidence / 20 Synthesis / 30 Analysis = OK / NG`
- `Highest Severity = Minor / Moderate / Major / empty`
- `Reviewed At`

artifact-level OK / NGは独立した手入力判定にしない。canonical Findingからdeterministically導出する。

- transitionにFindingがあれば、そのtransition target artifactをNGとする。
- Findingの `repair_direction.affected_layer` もNGとする。
- このため、既存schemaへ別の手入力verdictを追加せず `00_context` のNGも表現できる。
- FindingがないartifactはOKとする。

Review page bodyは少なくとも次をdeterministically renderする。

1. `Summary`
2. `Next Action — Quick Reference`
3. `Review Details`
4. `Provenance`

Next ActionはFindingの `repair_direction.mode / affected_layer / instruction` とWorkflow 10 invalidation ruleから導出する。Reviewerやconnectorがad hocに次手を作文してcanonical ruleを上書きしない。

### Investigation pointer

Investigations DBには次を保持する。

- `Review Status`: BKL-0027のprocess state
- `Latest Review`: latest projected Review rowへのrelation
- `Latest Review Seq`: compatibility pointerとして当面維持

human navigationは `Latest Review` relationを優先する。`Latest Review Seq` はBKL-0032で削除せず、既存contractとの互換性のため保持する。

### Deterministic adapter / fail-stop

canonical helperは `src/research_atelier/projection/review.py` とする。

adapterは少なくとも次を満たす。

- Git Review historyをvalidationしlatest cycleを解決する。
- Investigation IDがNotion Investigations DBでexactly one rowへ解決することを確認する。
- `(Investigation ID, Review Seq)` がReviews DBで0または1 rowへ解決することを確認する。
- 0 rowならcreate、1 rowならcanonical renderingへupdate / NOOP、2 row以上ならBLOCKED。
- Review row成立後に `Latest Review` relationを同期する。
- 同一Git factsで再実行した場合は追加rowを作らずNOOPへ収束する。
- canonical history invalid、Investigation binding不明/重複、Review projection row重複では推測してmutationしない。

Review Status transitionは引き続き `src/research_atelier/reviewing/reconcile.py` が所有し、Review DB導入を理由にstate machineを二重実装しない。


## 16. BKL-0034 split persistence implementation

canonical helper implementation:

- `src/research_atelier/reviewing/review_writer.py`: target freeze、cycle-global Finding ID、4 layer + manifest validation、append-only finalize。
- `src/research_atelier/reviewing/review_state.py`: legacy / split history validationとnormalized Review Cycle生成。
- `src/research_atelier/projection/review.py`: normalized cycleからReviews DB projectionを生成。
- `src/research_atelier/reviewing/reconcile.py`: storage-neutral `review_seq / verdict / target` を用いる既存state machineを継続。

新規schema分割を理由にReviews DBのlogical identityやInvestigations.`Latest Review` relationを再設計しない。
