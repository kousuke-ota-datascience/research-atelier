# Workflow 00 — Research Investigation Orchestration

## 0. 位置付け

Workflow 00は、1つのResearch Investigation全体を統括するtop-level orchestration contractである。

以下を決定する。

- current Investigation state
- 安全に再開できる最も早い地点
- upstream変更後にdownstream artifactがstaleかどうか
- Workflow 10をいつ実行するか
- Investigationをいつfinalizeできるか
- Git -> NotionのWorking Answer projectionを適用すべきか

Workflow 00自身は、Source discovery、Evidence selection、Synthesis、Analysisの意味論を再実装しない。これらはWorkflow 10の責務である。

JSON Schemaやlineage validationも再実装しない。deterministic validatorへ委譲する。

## 1. Public input

通常のbusiness inputは、1つのResearch Questionまたは1つのInvestigation IDとする。

RQだけが与えられ、Investigation IDが指定されていない場合:

1. そのRQに紐づく未完了Investigationを確認する。
2. current workとして再開すべき同一executionが存在するか判定する。
3. 再開対象がなければ `0002_investigation_versioning.md` に従って新しい `INV-NNNNNN` をglobal sequenceから採番する。

v2 Investigation IDはRQ IDをencodeしない。RQとのbindingは `00_context.rq_id` で行う。

内部artifact pathやvalidator stageを導出できる場合、それらを通常のuser inputとして要求しない。

## 2. Derived state model

stateはcurrent artifactとvalidation resultから導出する。第二のauthoritative status fieldとして保存しない。

### NEW

定義:

- 採番済みInvestigationに `00_context.json` が存在しない。

処理:

- Workflow 10をcontext constructionから開始する。

### PARTIAL

定義:

- 少なくとも1つcanonical artifactが存在する。
- 既存の連続prefixはvalidである。
- 1つ以上のdownstream artifactがmissingである。

例:

- 00は存在しPASS、10がmissing
- 00 / 10はPASS、20がmissing
- 00 / 10 / 20はPASS、30がmissing

処理:

- earliest missing artifactから再開する。

### INVALID

定義:

- 既存artifactがdeterministic validationでFAILする、または
- known upstream semantic changeにより、downstream JSONがschema-validでもsemanticにinvalidatedされている。

処理:

- earliest invalid artifactを特定する。
- そのstageからrepair / reconstructする。
- downstreamを再度trustする前にすべてrevalidateする。

### VALIDATED

定義:

- 00 / 10 / 20 / 30がすべて存在する。
- `validate_investigation <ID> --through 30` がPASSを返す。
- current chainをinvalidateするknown upstream changeがない。
- current analysisについてfinalization / accepted Working Answer projectionが未完了である。

処理:

- Workflow 10のcompletion conditionを確認する。
- current Investigationのanalysisをacceptする場合、projection contractを適用する。

### COMPLETE

定義:

- 4 canonical artifactがすべて存在する。
- through-30 deterministic validationがPASSする。
- Workflow 10のcompletion conditionを満たす。
- current `30_analysis` が当該Investigationのcurrent resultとしてacceptされている。
- `30_analysis.working_answer.text` が対応するNotion Research Questionへ正常にprojectionされている。
- unappliedなknown upstream changeがない。

Workflow 00を再実行した場合、COMPLETEを認識しcanonical artifactを不要に書き換えない。

### BLOCKED

定義:

external / semantic prerequisiteを解消しない限り進行できない状態。

例:

- RQ identityを解決できない。
- Investigation ownership / RQ bindingがambiguous。
- 必要なNotion / Git accessがない。
- assumptionを捏造せずにInvestigation Contextをfreezeできるほど明確化できない。
- canonical contract間にlocalでは解消不能な矛盾がある。

処理:

- exact blockerを報告して停止する。
- BLOCKEDを抜けるためにartifactをfabricateしない。

### ERROR

定義:

workflow machinery自体を信頼して動かせない状態。

例:

- schemaをloadできない。
- validatorがERRORを返す。
- repository writeが失敗し、completion stateが不確実になる。

処理:

- 停止する。
- last known canonical stateを保持する。
- ERRORをresearch failureとして解釈しない。

## 3. State derivation algorithm

Investigation `ID` に対して:

1. `investigations/ID/` と `00_context.json` の存在を確認する。
2. 00がなければstate = NEW。
3. through 00をvalidateする。
   - FAIL -> 00でINVALID
   - ERROR -> ERROR
4. 10がなければPARTIAL、resume = 10。
5. through 10をvalidateする。
   - FAIL -> reportされた00 / 10 errorのうちearliestでINVALID
   - ERROR -> ERROR
6. 20がなければPARTIAL、resume = 20。
7. through 20をvalidateする。
   - FAIL -> reportされた00 / 10 / 20 errorのうちearliestでINVALID
   - ERROR -> ERROR
8. 30がなければPARTIAL、resume = 30。
9. through 30をvalidateする。
   - FAIL -> reportされたearliest stageでINVALID
   - ERROR -> ERROR
10. 全段階PASSならVALIDATED。
11. current analysisのaccepted-result projectionが完了済みか確認する。
   - yes -> COMPLETE
   - no -> finalize / projectし、成功後COMPLETE

validator resultはdeterministic validityに関する事実であり、semantic quality scoreではない。

## 4. Earliest-resume rule

常に以下のうち最も早いartifactから再開する。

1. missing
2. deterministically invalid
3. changed upstream artifactによってsemantically invalidated

例:

| Current fact | Resume |
| --- | --- |
| artifactなし | 00 |
| 00 PASS、10 missing | 10 |
| 00 / 10 PASS、20 missing | 20 |
| through20 PASS、30 missing | 30 |
| 30存在後に10変更 | 20を再評価し、その後30 |
| 20変更 | 30を再評価 |
| 30のみ変更 | 30をvalidate / finalize |

Workflowを再実行したという理由だけで00からやり直さない。

## 5. Invalidation rule

dependency:

`00_context -> 10_evidence -> 20_synthesis -> 30_analysis`

upstream artifactがsemantically変更された場合:

| Changed artifact | 再評価されるまでstaleと扱う |
| --- | --- |
| 00 | 10, 20, 30 |
| 10 | 20, 30 |
| 20 | 30 |
| 30 | 30のみ |

downstream fileがbyte-for-byteで存在していてもinvalidatedされ得る。

したがって、file existenceだけでcurrencyを証明してはならない。

context-defining changeがfreeze後に発生した場合、またはaccepted resultをsubstantively reopenする場合は、historyを書き換えず新しいInvestigationを作る。

## 6. Near-idempotent rerun rule

inputが変わらない限り、再実行は同じcanonical stateへ収束するべきである。

rule:

- Workflow 00を再実行しただけで新しいInvestigationを採番しない。
- upstream inputが変わらずsemantic correctionも不要なら、PASS済みartifactを再生成しない。
- timestamp更新だけを目的にfileを書き換えない。
- semantic reasonなしにE / K / J identifierをrenumberしない。
- Notionがcurrent accepted Git answerと一致している場合、Working Answerを再projectionしない。
- projectionだけがstaleなら、derived Notion Working Answerだけを更新しGitは変更しない。
- validationはdeterministicなので安全に再実行してよい。

external Evidence discoveryやresearcherの明示的decisionによってinputが正当に変わり得るため、idempotenceはabsoluteではなくnear-idempotentとする。

## 7. Finalization と Working Answer projection

stateがVALIDATEDに到達したら:

1. Workflow 10のcompletion conditionを確認する。
2. pendingなknown Evidence / context changeがないことを確認する。
3. current `30_analysis` を当該Investigationのaccepted resultとして扱う。
4. `30_analysis.working_answer.text` をNotion `Research Questions.Working Answer` へprojectionする。
5. `0006_notion_git_projection_contract.md` に従い、target RQ、Investigation ID、Git commit SHA、timestamp、success / failureをlogする。
6. projection成功後、state = COMPLETE。
7. projection失敗時はGitがauthorityのまま、成功するまでstate = VALIDATED。

projectionはnarrowに保つ。Workflow 00はGitから他のNotion DB全体をsyncしない。

## 8. MVPで必須にしないもの

MVPでは以下を必須としない。

- independent semantic Review workflow
- Review sequence number
- review-target SHA freeze
- Git ancestry control-plane logic
- NotionへのSHA synchronization
- persistent orchestration state machine
- automatic Notion Status change
- Workflow 90型のcontrol-plane reconciliation

E2E pilotで具体的な必要性が確認された場合のみ後から導入する。

通常のGit commitはprovenanceとして残すが、専用SHA control planeをCOMPLETEの前提にはしない。

## 9. Completion report

Workflow 00の実行結果では少なくとも以下を報告する。

- `investigation_id`
- derived state: NEW / PARTIAL / INVALID / VALIDATED / COMPLETE / BLOCKED / ERROR
- COMPLETEでない場合のearliest resume stage
- latest deterministic validation result
- invalidated downstream artifactの有無
- Working Answer projectionがcurrentか
- BLOCKED / ERROR時のdetail

## 10. Invariant

Workflow 00はorchestratorであり、alternate source of truthではない。

stateは次から導出する。

- canonical Git artifact
- deterministic validation
- authority / versioning / projection contract
- そのcatalogがauthorityを持つ範囲のcurrent Notion state

old downstream artifactを、fileが存在するという理由だけでtrustedにしてはならない。


## 11. v1 legacy handling

既存 `RQ-NNNN-vVVV` Investigationをorchestrateする場合はlegacy v1 identity / schemaを維持する。新規executionではlegacy IDを採番せず、`INV-NNNNNN` を使用する。
