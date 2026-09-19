# Task 14 — Semantic Review / Control Plane高度化のpilot後再評価

## 1. Decision

Research MVPでは、現時点で以下を必須実装しない。

- independent Semantic Review workflow
- Review Seq
- review targetのcommit / blob SHA freeze
- NotionへSHAを同期するControl Plane
- Git ancestryを用いたreconciliation
- persistent orchestration state machine

既存のWorkflow 00 / Workflow 10、Investigation versioning、artifact invalidation、deterministic validation、Gitのoptimistic concurrencyでMVPを継続する。

これは「将来も不要」という判断ではなく、**今回のpilotでは追加complexityを正当化するfailure modeが観測されなかったためdeferする**という判断である。

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

MVPではindependent Semantic Review cycleそのものを必須化しないため、review target freezeも必須化しない。

将来Review workflowを導入する場合は、review対象を最低でも次で固定する。

- `investigation_id`
- reviewed `30_analysis` を含むGit commit SHA、またはartifact blob SHA
- review timestamp

review中にcanonical artifactが更新された場合、old review verdictをnew artifactへ流用しない。

## 6. 将来導入する場合の責務分離

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

Task 12 pilot後の判断は次のとおり。

> **MVPではSemantic Review / SHA Control Plane高度化を導入しない。既存のversioning、invalidation、deterministic validation、Git optimistic concurrencyで運用を継続し、上記triggerが観測された時点で再評価する。**

これにより、観測されていない問題に対する基盤を先行実装せず、必要になった機構だけを追加する。
