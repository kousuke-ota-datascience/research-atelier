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

## 5. Reviewするsemantic transition

Reviewはcanonical chainの順序を維持する。

### 5.1 Source / Evidence Note provenance -> `10_evidence`

確認対象:

- Evidence contentがSourceへtraceでき、source-faithfulか。
- quote / paraphrase / locator / provenanceが意味論上妥当か。
- selectionによって重要な反証・qualification・uncertaintyが不当に落ちていないか。
- Notion Evidence Noteとfrozen Evidence snapshotの意味が変質していないか。

Source上の情報を直接Analysisへ持ち込んで不足を補完しない。Evidence layerの不足はupstream findingとして扱う。

### 5.2 `10_evidence` -> `20_synthesis`

確認対象:

- knowledge unitが参照Evidenceでsupportされるか。
- unsupported propositionや過剰一般化がないか。
- disagreement / conflict / uncertainty / qualificationが消失していないか。
- cross-source synthesisとSource自身のclaimが区別されているか。
- downstream Analysisに必要なmeaningを作るためEvidenceを越えていないか。

### 5.3 `20_synthesis + 00_context` -> `30_analysis`

確認対象:

- frozen RQ / Scope / assumptionsに対するRQ-specific inferenceになっているか。
- `question_type` 固有のmethodological validityを満たすか。
- Judgment / Working AnswerがSynthesisを越えて断定していないか。
- limitation / alternative explanation / unresolved questionが重要な不確実性を保持しているか。
- raw Evidence / Sourceを直接使って `20_synthesis` をbypassしていないか。

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

保存先:

```text
investigations/<Investigation ID>/reviews/
  review-000001.json
  review-000002.json
  ...
```

1 Review cycle = 1 JSONとし、3 semantic transitionを同一cycleへ集約する。

1. `source_evidence_note_to_10_evidence`
2. `10_evidence_to_20_synthesis`
3. `20_synthesis_plus_00_context_to_30_analysis`

canonical schema:

- `schemas/v2/review_cycle.schema.json`
- common Finding definitions: `schemas/v2/review_common.schema.json`

各recordは少なくとも次を保持する。

- `schema_version`
- `investigation_id`
- `review_seq`
- target commit SHA
- 00 / 10 / 20 / 30 blob SHA
- `reviewed_at`
- transition別semantic assessment
- Findings
- deterministic Verdict

Finding identityはcycle-local `F001...` とし、logical identityは `(Investigation ID, Review Seq, Finding ID)` で表す。

Findingは次を持つ。

- `severity = Minor / Moderate / Major`
- `target`
- canonical artifact上の `evidence` reference
- `impact`
- `repair_direction.mode = same_investigation / new_investigation`
- `repair_direction.affected_layer = 00_context / 10_evidence / 20_synthesis / 30_analysis`
- repair instruction

cycle-level VerdictはReviewerが独立入力しない。writerがFinding集合からdeterministically算出する。

- Finding 0件 -> `PASS`
- Finding 1件以上 -> `FINDINGS`

`STALE / BLOCKED` はcanonical semantic Verdictではなく、target relation / execution conditionからreconcilerが導出するworkflow outcomeである。

Markdown Reviewは作成してもderived viewであり、Review history / completion / reconciliationの事実源にしない。

## 10. Repair handoff

Reviewerとrepair executorの責務を分離する。

findingのrepair開始位置:

| Finding target | Repair start | Downstream handling |
| --- | --- | --- |
| `00_context` semantic condition | versioning contractに従い、freeze後なら原則new Investigation | new INVで10/20/30を構築 |
| Source / Evidence / `10_evidence` | Workflow 10 Evidence stage | 20 / 30をinvalidate |
| `20_synthesis` | Workflow 10 Synthesis stage | 30をinvalidate |
| `30_analysis` のみ | Workflow 10 Analysis stage | 30をrepair / revalidate |

ただしaccepted Investigationのsubstantive repairは `0002_investigation_versioning.md` を優先する。historical accepted resultを書き換える必要があるrepairなら、新Investigationを作る。

repair後は新しいtarget SHA / blobをfreezeし、old Review outcomeを流用せずreReviewする。

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
- Review common / cycle JSON Schema
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
