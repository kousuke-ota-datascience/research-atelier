# Workflow 00 — Research Investigation Orchestration

## 0. 位置付け

Workflow 00は、1つのResearch Investigation全体を統括するtop-level orchestration contractである。

以下を決定する。

- current Investigation state
- 安全に再開できる最も早い地点
- upstream変更後にdownstream artifactがstaleかどうか
- Workflow 10をいつ実行するか
- optional Workflow 20を明示的に要求するか
- Investigationをいつfinalizeできるか
- Git -> NotionのWorking Answer projectionを適用すべきか

Workflow 00自身は、Source discovery、Evidence selection、Synthesis、Analysisの意味論を再実装しない。これらはWorkflow 10の責務である。

independent Semantic Reviewを実行する場合、その意味論的assessmentはWorkflow 20へ委譲する。Workflow 00自身がReviewerにならない。

JSON Schemaやlineage validationも再実装しない。deterministic validatorへ委譲する。

## 1. Public input

通常のbusiness inputは、**人間が意味を定義し採択した1つのResearch Question**、または1つの既存Investigation IDとする。未採択の会話上の問いを、Workflow 00自身がcanonical Research Questionとして暗黙に生成してはならない。

RQだけが与えられ、Investigation IDが指定されていない場合:

0. Research Questionがacceptedであり、「このRQを調査する」というhuman research intentが成立していることを確認する。

1. そのRQに紐づく未完了Investigationを確認する。
2. current workとして再開すべき同一executionが存在するか判定する。
3. 再開対象がなければ `0002_investigation_versioning.md` に従って新しい `INV-NNNNNN` をglobal sequenceから採番する。

v2 Investigation IDはRQ IDをencodeしない。RQとのbindingは `00_context.rq_id` で行う。

内部artifact pathやvalidator stageを導出できる場合、それらを通常のuser inputとして要求しない。

### 1.1 Entrance contract

Workflow 00の責務は**accepted Research Questionからcanonical research executionへhandoffすること**であり、Research Questionのsemantic formulation / acceptanceそのものではない。

入口条件:

- 新規research: accepted Research Questionが存在し、human research intentが確認されている。
- resume: 既存Investigation IDが与えられ、そのRQ bindingとlifecycleを解決できる。
- RQ wording整理や候補提示はLLMが支援してよいが、semantic target / Scope / assumptions等のhuman-owned commitmentを暗黙に確定しない。
- semantic question identityが未確定なら、Workflow 00はResearch executionを開始せず、RQ acceptanceが成立するまでBLOCKEDとする。

### 1.2 Canonical execution invariant

対象RQが存在し、外部Sourceを探索してsubstantive conclusionを生成する場合、その実行はWorkflow 00を経由し、Workflow 10のcanonical artifact chainへ接続しなければならない。

ad hocなWeb search / citation付きchat回答だけで substantive research を完了扱いしてはならない。Sources / Evidence Notes / canonical Investigation artifactを形成していない場合、その回答はResearch Atelier上のcanonical resultではなく **workflow incomplete / non-canonical** である。

したがって、ad hoc回答をResearch Question bodyの `# Working Answer` へcanonical projectionしたり、COMPLETEと判定したりしてはならない。

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
- acceptance前Workflow 20が明示的prerequisiteなら、そのReviewを完了する。
- current Investigationのanalysisをacceptする場合、projection contractを適用する。

### COMPLETE

定義:

- 4 canonical artifactがすべて存在する。
- through-30 deterministic validationがPASSする。
- Workflow 10のcompletion conditionを満たす。
- current `30_analysis` が当該Investigationのcurrent resultとしてacceptされている。
- 対応するNotion Research Question bodyのunique `# Working Answer` sectionがcurrent accepted `30_analysis` のdeterministic renderingと一致している。
- legacy `Research Questions.Working Answer` propertyの値はCOMPLETE判定へ使用しない。
- unappliedなknown upstream changeがない。
- defaultではWorkflow 20未実施をCOMPLETE阻害条件にしない。
- acceptance前Workflow 20が明示的prerequisiteとして要求された場合は、そのReviewが未完了またはcurrent targetにunresolved findingを持つ間はCOMPLETEにしない。

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
- target RQ bodyにtop-level `# Working Answer` headingが複数存在し、安全なprojection targetを一意に決められない。

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
11. acceptance前Workflow 20が明示的prerequisiteとして要求されている場合:
   - Review未実施 -> VALIDATEDのままReview pendingとして停止する。
   - BLOCKED -> state = BLOCKED。
   - STALE -> VALIDATEDのままcurrent targetをfreezeし直してreReviewする。
   - FINDINGS -> findingが示すearliest affected stageをsemantic INVALIDとしてrepair / reconstructする。
   - PASS -> finalizationへ進める。
   defaultではReviewを要求せず、このstepをskipする。
12. current accepted `30_analysis` とRQ bodyの `# Working Answer` projection stateを確認する。
   - unique sectionがdeterministic renderingと一致する = CURRENT -> COMPLETE
   - section missing = MISSING -> finalize / project
   - unique sectionが異なる = STALE -> body sectionだけをreproject
   - target headingが複数 = BLOCKED -> bodyを推測更新しない
13. MISSING / STALEをprojectした場合、RQ pageを再取得してCURRENTを確認してからCOMPLETEとする。write / verification failureではVALIDATEDのままとする。

legacy `Research Questions.Working Answer` propertyのempty / legacy / stale valueはこのstate derivationへ参加しない。

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
- RQ bodyのunique `# Working Answer` sectionがcurrent accepted `30_analysis` のdeterministic renderingと一致する場合、再projectionしない。
- projectionだけがMISSING / STALEなら、derived body sectionだけを更新しGit artifactとlegacy propertyは変更しない。
- timestamp更新だけを理由にbody sectionをrewriteしない。
- validationはdeterministicなので安全に再実行してよい。

external Evidence discoveryやresearcherの明示的decisionによってinputが正当に変わり得るため、idempotenceはabsoluteではなくnear-idempotentとする。

## 7. Finalization と Working Answer projection

stateがVALIDATEDに到達したら:

1. Workflow 10のcompletion conditionを確認する。
2. pendingなknown Evidence / context changeがないことを確認する。
3. acceptance前Workflow 20が明示的prerequisiteとして要求されている場合、`0020_semantic_review.md` に従いcurrent targetをReviewし、PASSであることを確認する。FINDINGS / STALE / BLOCKEDではfinal acceptanceへ進まない。
4. current `30_analysis` を当該Investigationのaccepted resultとして扱う。
5. `src/research_atelier/projection/working_answer.py` のdeterministic rendererでstructured `# Working Answer` sectionを生成する。
6. RQ page bodyを取得し、`0006_notion_git_projection_contract.md` のsafe body update semanticsに従ってtarget sectionだけをcreate / replaceする。
7. top-level `# Working Answer` が複数ならBLOCKEDとし、どれを更新するか推測しない。
8. Notion write後にRQ pageを再取得し、body sectionがcurrent accepted renderingと一致することを確認する。
9. target RQ、RQ ID、Investigation ID、accepted `30_analysis` commit SHA、timestamp、body target、success / failureを `projection_log_v2.json` としてlogする。historical `projection_log.json` はrewriteしない。
10. verification成功後、state = COMPLETE。
11. projection write / verification失敗時はGitがauthorityのまま、成功するまでstate = VALIDATED。

legacy `Research Questions.Working Answer` propertyは削除しないが、projection targetへdual-writeせずCOMPLETE判定にも使用しない。

projectionはnarrowに保つ。Workflow 00はGitから他のNotion DB全体をsyncしない。

## 8. Optional Workflow 20 / MVPで必須にしないもの

Workflow 20はoptional independent Semantic Reviewとして `0020_semantic_review.md` に定義する。

default運用ではReview未実施をCOMPLETE阻害条件にしない。Reviewを実行する場合は、targetをInvestigation ID + commit / artifact blob SHA + timestampで固定する。

一方、MVPでは以下を必須としない。

- Workflow 20を全Investigationのdefault completion gateにすること
- Review sequence number
- persistent Review JSON / dedicated Review Schema / writer
- persistent review-target SHA control plane
- Git ancestry control-plane logic
- NotionへのSHA synchronization
- persistent orchestration state machine
- automatic Notion Status change
- Workflow 90型のcontrol-plane reconciliation

BKL-0021 pilotではoptional Semantic Reviewの有用性は確認したが、mandatory gate / persistent Review infrastructureを正当化する反復failureは観測していない。

通常のGit commitはprovenanceとして残すが、専用SHA control planeをdefault COMPLETEの前提にはしない。

## 9. Completion report

Workflow 00の実行結果では少なくとも以下を報告する。

- `investigation_id`
- derived state: NEW / PARTIAL / INVALID / VALIDATED / COMPLETE / BLOCKED / ERROR
- COMPLETEでない場合のearliest resume stage
- latest deterministic validation result
- invalidated downstream artifactの有無
- Working Answer body projection state: MISSING / STALE / CURRENT / BLOCKED
- Workflow 20を明示的に実行した場合のみReview outcome: PASS / FINDINGS / STALE / BLOCKED
- BLOCKED / ERROR時のdetail

## 10. Invariant

Workflow 00はorchestratorであり、alternate source of truthではない。

Human / Researcherが所有するのはresearch intentとsemantic commitmentsであり、Workflow 00が所有するのはInvestigation lifecycle / identity allocation / orchestrationである。Workflow 00はResearch Questionを生成・採択するauthorityを持たない。

stateは次から導出する。

- canonical Git artifact
- deterministic validation
- authority / versioning / projection contract
- そのcatalogがauthorityを持つ範囲のcurrent Notion state

old downstream artifactを、fileが存在するという理由だけでtrustedにしてはならない。


## 11. Regression scenario — accepted RQをchatだけで調査してしまうケース

以下をTask 18の回帰シナリオとして扱う。

1. Humanが深掘り質問を提示し、LLM支援でResearch QuestionとしてNotionへmaterializeした。
2. そのRQに対して外部Web Sourceを探索し、citation付きのsubstantive answerをchat上で生成した。
3. Workflow 00へhandoffせず、Investigation IDを解決・採番しなかった。
4. Sources / Evidence Notesをcaptureせず、`10_evidence` / `20_synthesis` / `30_analysis` を作成しなかった。
5. それでも回答済みと扱った。

この状態は**Research Atelier上では未完了**である。理由は、回答からSourceへ遡るcanonical Evidence lineageと、frozen execution conditionを持つInvestigationが存在しないためである。

期待動作:

- accepted RQに対するsubstantive research開始時点でWorkflow 00へ入る。
- resume可能なInvestigationがなければ新しい `INV-NNNNNN` を採番する。
- Workflow 10を通してSource / Evidence lineageとcanonical artifactsを構築する。
- through-30 validationとaccepted result projectionが完了するまでCOMPLETEにしない。
- chat上のad hoc answerはcanonical Working Answerのsourceとして扱わない。

## 12. v1 legacy handling

既存 `RQ-NNNN-vVVV` Investigationをorchestrateする場合はlegacy v1 identity / schemaを維持する。新規executionではlegacy IDを採番せず、`INV-NNNNNN` を使用する。
