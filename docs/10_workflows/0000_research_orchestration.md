# Workflow 00 — Research Investigation Orchestration

## 0. 位置付け

Workflow 00は、1つのResearch Investigation全体を統括する最上位orchestration contractである。

本Workflowが決めるのは以下である。

- current Investigation state
- 最も早い安全なresume point
- upstream変更後にdownstream artifactがstaleか
- Workflow 10をどこから実行するか
- Investigationをいつfinalizeできるか
- Git -> Notion Working Answer projectionを適用すべきか

Workflow 00自身は、Source discovery、Evidence selection、Synthesis、Analysisの意味論を再実装しない。これらはWorkflow 10の責務である。

JSON Schema / lineage validationも再実装しない。deterministic validatorへ委譲する。

## 1. Public input

通常の業務入力は、1つのResearch Questionまたは1つのInvestigation IDとする。

RQだけが与えられた場合:

1. existing Investigation versionを確認する。
2. unfinished versionを安全にresumeできるか判定する。
3. resumeできなければ `0002_investigation_versioning.md` に従って次versionを採番する。

artifact pathやvalidator stageなど導出可能な内部情報を、通常のユーザー入力として要求しない。

## 2. Derived state model

stateはcurrent artifactとvalidation resultから**導出**する。第二のauthoritative status fieldとして保存しない。

### NEW

定義:

- allocated Investigationに `00_context.json` が存在しない。

Action:

- Workflow 10をcontext constructionから開始する。

### PARTIAL

定義:

- 1つ以上のcanonical artifactが存在する。
- 存在する連続prefixはvalid。
- downstream artifactが1つ以上missing。

例:

- 00 PASS、10 missing
- 00 / 10 PASS、20 missing
- 00 / 10 / 20 PASS、30 missing

Action:

- earliest missing artifactからresumeする。

### INVALID

定義:

- existing artifactがdeterministic validation FAIL。
- または、known upstream semantic changeによりdownstream artifactがinvalidatedされている。JSON自体がschema-validでも該当する。

Action:

- earliest invalid artifactを特定する。
- そのstageからrepair / reconstructする。
- downstreamを再validationするまで信用しない。

### VALIDATED

定義:

- 00 / 10 / 20 / 30がすべて存在する。
- `validate_investigation <ID> --through 30` がPASS。
- known upstream changeによるinvalidationが残っていない。
- current analysisについてfinalization / accepted Working Answer projectionが未完了。

Action:

- Workflow 10 completion conditionを確認する。
- current InvestigationのAnalysisをacceptするならprojection contractを適用する。

### COMPLETE

定義:

- 4 canonical artifactが存在する。
- through-30 deterministic validationがPASS。
- Workflow 10 completion conditionを満たす。
- current `30_analysis` がこのInvestigationのcurrent resultとしてaccepted。
- `30_analysis.working_answer.text` が対応するNotion Research Questionへprojection済み。
- known upstream changeが未反映で残っていない。

Workflow 00を再実行しても、COMPLETEならcanonical artifactを不要に書き換えない。

### BLOCKED

定義:

external / semantic prerequisiteを解消しない限り進行不能な状態。

例:

- RQ identityを解決できない。
- Investigation versionのownershipが曖昧。
- 必要なNotion / Git accessがない。
- assumptionを捏造しないとResearch Contextをfreezeできない。
- canonical contract間にlocalで解消不能な矛盾がある。

Action:

- exact blockerを報告して停止する。
- BLOCKEDを回避するための架空artifactを作らない。

### ERROR

定義:

workflow machinery自体を信頼して実行できない状態。

例:

- schemaをloadできない。
- validatorがERROR。
- repository write failureで完了状態が不明。

Action:

- 停止する。
- last known canonical stateを保存する。
- ERRORをresearch failureへ読み替えない。

## 3. State derivation algorithm

Investigation `ID` について:

1. `investigations/ID/` と `00_context.json` の存在を確認する。
2. 00がない -> NEW。
3. through 00でvalidateする。
   - FAIL -> INVALID at 00
   - ERROR -> ERROR
4. 10がない -> PARTIAL、resume 10。
5. through 10でvalidateする。
   - FAIL -> earliest 00/10 errorからINVALID
   - ERROR -> ERROR
6. 20がない -> PARTIAL、resume 20。
7. through 20でvalidateする。
   - FAIL -> earliest 00/10/20 errorからINVALID
   - ERROR -> ERROR
8. 30がない -> PARTIAL、resume 30。
9. through 30でvalidateする。
   - FAIL -> earliest reported stageからINVALID
   - ERROR -> ERROR
10. 全てPASS -> VALIDATED。
11. current analysisのaccepted-result projectionが完了済みか確認する。
   - yes -> COMPLETE
   - no -> finalize / projectし、成功後COMPLETE

validator resultはdeterministic validityの証拠であり、semantic quality scoreではない。

## 4. Earliest-resume rule

常に以下のうち最も上流にあるartifactからresumeする。

1. missing
2. deterministically invalid
3. changed upstreamによりsemantically invalidated

| Current fact | Resume |
| --- | --- |
| artifactなし | 00 |
| 00 PASS、10 missing | 10 |
| 00 / 10 PASS、20 missing | 20 |
| through20 PASS、30 missing | 30 |
| 10変更後に30が残っている | 20を再評価し、その後30 |
| 20変更 | 30を再評価 |
| 30のみ変更 | 30をvalidate / finalize |

Workflowを再実行しただけで00からやり直さない。

## 5. Invalidation rule

dependency:

`00_context -> 10_evidence -> 20_synthesis -> 30_analysis`

upstream artifactがsemanticに変更された場合:

| Changed artifact | re-evaluateされるまでstale |
| --- | --- |
| 00 | 10, 20, 30 |
| 10 | 20, 30 |
| 20 | 30 |
| 30 | 30のみ |

downstream fileがbyte-for-byteで存在していてもinvalidatedされうる。

したがってfile existenceだけでcurrencyを証明できない。

freeze後のcontext-defining changeやaccepted resultの実質的reopenでは、historical artifactを書き換えずInvestigation versioning contractを適用する。

## 6. Near-idempotent rerun rule

inputが変わっていなければ、再実行は同じcanonical stateへ収束するべきである。

- Workflow 00再実行だけを理由に新Investigation versionを採番しない。
- upstream input不変かつsemantic correction不要ならPASS済みartifactを再生成しない。
- timestamp更新だけのためにfileを書き換えない。
- semantic reasonなしにE/K/J identifierを振り直さない。
- Notionがaccepted current Git answerと一致するならWorking Answerを再projectionしない。
- projectionだけstaleならderived Notion Working Answerのみ更新し、Gitは変更しない。
- validationはdeterministicなので繰り返し実行してよい。

external Evidence discoveryや明示的なresearcher decisionでinputが変わりうるため、absoluteではなくnear-idempotentとする。

## 7. Finalization / Working Answer projection

stateがVALIDATEDになったら:

1. Workflow 10 completion conditionを確認する。
2. 未反映のknown Evidence / Context changeがないことを確認する。
3. current `30_analysis` をこのInvestigationのaccepted resultとする。
4. `30_analysis.working_answer.text` をNotion `Research Questions.Working Answer` へprojectionする。
5. `0006_notion_git_projection_contract.md` に従い、target RQ、Investigation ID、Git commit SHA、timestamp、success / failureをlogする。
6. projection成功後、state = COMPLETE。
7. projection失敗時はGitが正本のまま。stateはVALIDATEDに留め、projectionをretryする。

projectionは狭く保つ。Workflow 00はGitからNotion Research DB全体をsyncしない。

## 8. MVP exclusions

MVPでは以下を必須にしない。

- independent semantic Review workflow
- Review Seq
- review-target SHA freeze
- Git ancestry control-plane logic
- SHAのNotion同期
- persistent orchestration state machine
- automatic Notion Status change
- Workflow 90型control-plane reconciliation

E2E pilotで具体的必要性が確認された場合にのみ導入を再検討する。

Git commitは通常のprovenanceとして保持するが、専用SHA control planeをCOMPLETE条件にはしない。

## 9. Completion report

Workflow 00の実行結果は少なくとも以下を報告する。

- `investigation_id`
- derived state: NEW / PARTIAL / INVALID / VALIDATED / COMPLETE / BLOCKED / ERROR
- COMPLETEでない場合のearliest resume stage
- latest deterministic validation result
- invalidated downstream artifactの有無
- Working Answer projectionがcurrentか
- BLOCKED / ERROR時の詳細

## 10. Invariant

Workflow 00はorchestratorであり、別のsource of truthではない。

stateは以下から導出する。

- canonical Git artifacts
- deterministic validation
- authority / versioning / projection contract
- Notionがauthorityを持つ箇所だけcurrent Notion catalog state

古いdownstream artifactを「fileがある」という理由だけで信用してはならない。
