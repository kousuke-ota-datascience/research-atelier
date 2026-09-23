# Task 14 — Semantic Review / Control Plane高度化のpilot後再評価

## 1. Decision

Task 14時点では、以下をMVP必須実装からdeferした。

- Workflow 20をWorkflow 00のdefault completion gateとして必須化すること
- Review Seq
- persistent Review JSON / Review専用Schema / writer
- review target SHAを永続管理・同期する専用Control Plane
- NotionへSHAを同期するControl Plane
- full Git ancestry / sync reconciliation
- persistent orchestration state machine

その後のdecisionはBKL-0021 / BKL-0027で段階的にamendされた。

**BKL-0027 current decision:**
- Workflow 20をdefault mandatory gateにしない、というdecisionは維持する。
- Workflow 20を実行した場合のper-Investigation Review Seq、append-only Review JSON、dedicated Review Schema / writer / read-only history loader、Review Status reconcilerは採用する。
- Review target commit / artifact blob SHAはReview JSON内のcanonical audit factとして永続化する。
- NotionへSHA propertyを追加する専用Control Plane、artifact単位のStatus row、full Git ancestry sync control planeは引き続きdeferする。

したがってTask 14はhistorical decision recordであり、current normative contractはWorkflow 20 / Workflow 00 / projection contractを参照する。

## 2. Pilotで観測したfailure mode

### F-01: Notion formula ID取得gap

Notion connectorからformula型 `RQ ID` のactual valueを直接取得できなかった。

これはNotion integration boundaryの問題であり、independent Semantic ReviewやSHA Control Planeでは解決しない。

対応: Task 15。

### F-02: evidence_cutoffの誤用によるv001 invalidation

`RQ-0003-v001` では、context freeze時刻を `evidence_cutoff` としたため、workflow中に生成したvalidator resultを後からEvidenceへ含められなくなった。

frozen contextをin-place修正せず `RQ-0003-v002` を作成し、既存versioning ruleでhistoryを保持した。

これはResearch Context / versioning semanticsの問題であり、Review target freezeがなくても検出・修正できた。

対応: Task 16。

### F-03: Git更新時のconcurrent edit

document日本語化の途中、取得済みblob SHAがstaleになりGitHub Contents APIが409 Conflictを返した。

古いSHAによるupdateが拒否されたため、lost updateは発生しなかった。

最新版を再取得してcurrent SHAで更新することで安全に収束した。

このfailure modeに対しては、現状のGit optimistic concurrencyがminimum safety mechanismとして機能した。

## 3. Independent Semantic Reviewの必要性評価

今回のpilotでは、deterministic validationをPASSしたものの、独立したreviewerでなければ発見できないresearch-semantic errorは観測しなかった。

ただし、この結果を一般化して「Semantic Reviewは不要」とは結論しない。

今回のRQはJSON Schema設計を扱うMethodological questionであり、以下のようなResearchではsemantic riskが高い。

- Causal inference
- Mechanistic explanation
- conflicting empirical literatureのadjudication
- high-impact decisionに接続するWorking Answer
- extensive source selection / exclusion judgment

したがってMVPではoptionalとし、pilotを追加して必要性を再評価する。

## 4. stale artifact評価

stale artifactのrisk自体は実在する。

しかし現在は、以下で管理できる。

- dependency: `00 -> 10 -> 20 -> 30`
- upstream change時の明示的invalidation
- freeze後のcontext-defining changeはnew Investigation version
- `validate_investigation --through ...` によるdeterministic revalidation

今回、old downstream artifactをcurrentとして誤acceptした事例はなかった。

したがって、current MVPでは専用Control Plane DB / SHA同期を追加しない。

## 5. Review target freeze評価

Workflow 20はBKL-0021でoptional workflowとしてcanonicalizeした。Workflow 20自体をdefault completion gateにはしない。

ただし、**Workflow 20を実際に実行する個別Reviewではtarget freezeをminimum contractとする。**

最低でも次を固定する。

- `investigation_id`
- reviewed `30_analysis` を含むGit commit SHA、またはartifact blob SHA
- review timestamp

review中にcanonical artifactが更新された場合、old Review outcomeをnew artifactへ流用しない。

BKL-0027により、Review Seqとpersistent Review JSONは採用した。Review JSONはtarget commit SHAと00 / 10 / 20 / 30 blob SHAを保持し、current targetとのexact / stale判定に使用する。

一方、NotionへのSHA同期、専用pre/post SHA property、repository全体のfull Git ancestry control planeは引き続きdeferする。target ahead / diverged等、blob比較だけで安全に収束できないrelationはadapterがGit factsを解決できない限りBLOCKEDとする。

## 6. Semantic Review / Control Planeの責務分離

### Semantic Review

責務:

- Evidence-faithfulnessのsemantic確認
- Synthesisでの過剰一般化 / conflict消失の確認
- Question Type固有analysisの方法論的妥当性確認
- Working AnswerがEvidence / Synthesisを超えていないか確認
- limitation / alternative explanationの妥当性確認

担わない:

- Git / Notion synchronization
- SHA ancestry計算
- current state reconciliation

### Control Plane

責務:

- canonical artifact versionの識別
- review targetとcurrent artifactのstaleness判定
- projection state / sync stateの追跡
- concurrent edit / divergenceのdeterministic検出

担わない:

- research conclusionのsemantic judgment
- Evidence qualityの専門判断

この2責務を同じcomponentへ混在させない。

## 7. 導入trigger

以下のいずれかが実際に観測された場合、Semantic Review / Control Plane高度化を再度backlogへ上げる。

1. deterministic validation PASS後に、独立reviewで重大なsemantic errorが反復して見つかる。
2. 複数actorが同一Investigationを並行編集し、optimistic concurrencyだけでは運用が不安定になる。
3. review中にcanonical artifactが更新され、review verdictのtargetを一意に特定できない事象が発生する。
4. stale Working Answer projectionが反復し、Git / Notionのcurrent state判定が人手では管理困難になる。
5. regulated / high-stakes用途でindependent reviewがprocess requirementになる。

## 8. Conclusion

Task 12 pilot直後の判断は次のとおりだった。

> **当時のMVPではSemantic Review / SHA Control Plane高度化を導入せず、既存のversioning、invalidation、deterministic validation、Git optimistic concurrencyで運用を継続する。**

このhistorical decisionのうちSemantic Review部分は、BKL-0021により「未導入」から「optional Workflow 20を導入。ただしdefault mandatory gateではない」へamendした。

さらにBKL-0027により、persistent Review infrastructureのdeferを部分的に解除した。Review Seq / append-only Review JSON / Schema / writer / loader / deterministic Review current-state reconciliationを採用する。一方、Notion SHA propertiesやfull SHA Control Planeはdeferを継続する。


## 9. BKL-0021 amendment — optional Workflow 20

BKL-0021では `INV-000001` を対象にpilot Semantic Reviewを行った。詳細は `0015_semantic_review_pilot.md` を参照する。

pilotでは、deterministic validationでは扱わないsemantic support boundaryに関するfindingを確認した。

- Moderate: 1件
- Minor: 2件
- Major: 0件

Review targetはInvestigation ID + commit / artifact blob SHAで一意に固定でき、repair / reReviewも既存invalidation / Investigation lifecycleへmappingできた。

したがってTask 14 decisionを次のようにamendする。

1. **optional independent Semantic ReviewとしてWorkflow 20 contractを導入する。**
2. Workflow 20未実施だけを理由にWorkflow 00のVALIDATED / COMPLETEを阻害しない。
3. Human / Workflow 00がacceptance前Reviewを明示的に要求した場合、そのexecutionではReview completionをprerequisiteとして扱う。
4. BKL-0021時点ではReview Seq / persistent Review JSON / dedicated Review Schema / writerをdeferしたが、**この項目はBKL-0027でsupersedeされた**。
5. BKL-0027ではReview実行自体をmandatory化せず、実行されたReviewのpersistence / history / reconciliationだけをmandatory contractとした。
6. global Review ID、Review専用Notion DB、Notion SHA property、full SHA Control Planeは引き続き採用しない。
7. mandatory Review gateへ昇格するのは、Majorまたはmaterially consequential semantic findingの反復、regulated / high-stakes requirement等が観測された場合に再評価する。

つまりcurrent contractは、**Reviewはoptional / executed Review persistenceはmandatory**である。

## 10. BKL-0027 amendment — persistent Review contract

BKL-0027で次をcanonicalizeした。

- Review cycle identity: `(Investigation ID, Review Seq)`
- storage: `investigations/<Investigation ID>/reviews/review-<Review Seq:6 digits>.json`
- one cycle = one JSON containing the three Research semantic transitions
- target commit SHA + 00 / 10 / 20 / 30 blob SHA freeze
- Finding: severity / target / evidence / impact / repair direction
- deterministic cycle Verdict: `PASS / FINDINGS`
- Notion Investigations DB current pointer: `Review Status / Latest Review Seq`
- deterministic reconciler as the single transition / fail-stop / mutation-plan implementation

BKL-0027はTask 14のfull Control Plane deferを全面撤回するものではない。Review historyを安全に永続化しInvestigation current pointerを収束させる最小限のmechanical layerだけを導入した。

