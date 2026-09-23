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
- Review対象chainがcurrent deterministic contract上でvalidと扱える。
- canonical artifactがGitへcommitされている。
- Review対象版を一意に固定できる。

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

Review開始時に最低限、次を固定する。

- `investigation_id`
- reviewed `30_analysis` を含むGit commit SHA、または `30_analysis` artifact blob SHA
- `reviewed_at`

可能なら `00_context / 10_evidence / 20_synthesis / 30_analysis` の各blob SHAも記録する。

Review中にtargetを読み替えない。

### Staleness rule

次の場合、old Review outcomeをcurrent artifactへ流用しない。

- reviewed `30_analysis` blobが変わった。
- reviewed commitからcanonical artifactが更新された。
- upstream artifact変更によりreviewed downstreamがinvalidatedされた。
- repairにより新しいInvestigationが作られた。

Review中にtargetが更新された場合、旧targetに対するReviewはhistorical observationとしては残せるが、new targetのPass証明にはならない。new targetを再度freezeしてreReviewする。

SHA ancestry、current/staleの自動判定、projection / sync state追跡はControl Plane側のmechanical responsibilityであり、Semantic Reviewer自身の判断責務にしない。

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

## 9. Review outcome

BKL-0021時点のexecution-level outcomeは次とする。

- `PASS`: semantic findingなし。
- `FINDINGS`: 1件以上のfindingあり。
- `STALE`: review targetがexecution中またはその後に更新され、current artifactへoutcomeを適用できない。
- `BLOCKED`: target・provenance・required artifact等を一意に解決できずReview不能。

これは現時点ではpersistent canonical Review JSONのschema enumではない。

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

担わない:

- research conclusionのsemantic judgment
- Evidence qualityの専門判断

## 13. Persistent Review artifactを現時点で導入しない

BKL-0021では以下を**まだcanonical contractとして採用しない**。

- Review Seq
- Review JSON
- append-only review storage
- Review専用JSON Schema
- review writer
- persistent verdict history
- NotionへのReview SHA / state同期

理由は、pilotでSemantic Reviewの有用性は確認できた一方、persistent Review infrastructureを正当化する反復failure / concurrency / stale-target failureはまだ観測されていないためである。

将来persistent Review artifactを導入する場合は、authority、path、schema、versioning、writer、reReview、staleness、Workflow 00 integrationを別contractで同時に定義する。urban-legend版の `Entry_ID / Review_Seq` 実装をそのままcopyしない。

## 14. Invariant

Workflow 20は**Investigationに対する独立semantic assessment**であり、Research Questionの意味を所有せず、canonical artifact chainを迂回せず、deterministic validatorやControl Planeを再実装せず、findingとrepair executionを混同しない。
