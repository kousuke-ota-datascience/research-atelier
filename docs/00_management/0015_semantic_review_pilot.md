# BKL-0021 — Workflow 20 Semantic Review pilot

## 1. Purpose

BKL-0021の導入判断を、既存Investigation 1件へのpilot Reviewで検証した記録である。

評価する問い:

1. deterministic validationだけでは検出できないsemantic findingが実際にあるか。
2. Review targetを一意に固定できるか。
3. findingからrepair / reReviewへhandoffしても現行Investigation lifecycleと衝突しないか。
4. Workflow 20をmandatory gateへ昇格する根拠があるか。

## 2. Target

- Investigation: `INV-000001`
- Research Question: `RQ-0010`
- Question Type: `Methodological`
- reviewed `30_analysis` commit: `43446244778918ef1c3554dffbd99f82c16cc706`
- `00_context` blob: `d1a8b6715dc417b961d534a15286fbf6f37d7ed5`
- `10_evidence` blob: `6f5b966704c4cc42e694d89b91f79a1c7e492e45`
- `20_synthesis` blob: `e5f8239df9717c0b195793a0f13f436aa390b7a6`
- `30_analysis` blob: `4060d0d7141aefb0f7dd43d50bbcb60689c14887`
- review timestamp: `2026-09-22T23:58:30Z`

Review中にtargetを読み替えていない。

## 3. Preconditions / verification scope

canonical chain 4 artifactはGit上に存在し、同じ `investigation_id = INV-000001` / `rq_id = RQ-0010` を持つ。

このpilotではreview対象Investigation artifactを変更しておらず、Workflow 10で成立したcanonical chainへのsemantic assessmentを目的としたため、`validate_investigation --through 30` の再実行は不要と判断した。

Workflow 20の開始条件は、毎回CLIを再実行することではなく、対象chainがdeterministically validなcanonical targetとして扱えることである。再validationはtarget artifact / applicable validation contractの変更、known invalidation、validity不明、repair後のnew target等がある場合に行う。

provenance確認:

- `10_evidence` の17 Evidence itemについて、対応するNotion Evidence Note `EV-0031 ... EV-0047` とcontent / Source relation / locatorを照合した。
- 17件について明白なsnapshot転記不整合は観測しなかった。
- Source 8件のうち、今回のpilotでは主要claimに関係するpublisher / original-source pageを選択的に再確認した。全8 Sourceのfull-text再読を行ったsystematic re-reviewではない。

このscope limitationを、Source completenessの全面Pass証明として解釈しない。

## 4. Semantic Review result

Outcome: **FINDINGS**

Major findingは観測しなかった。Moderate 1件、Minor 2件を記録する。

### F-01 — weighted bias correctionをdefault first implementationとする推奨がsupport境界を越えている

- severity: **Moderate**
- target: `30_analysis.working_answer`, `J0002`
- evidence:
  - `K0001`: bias / offset updatingが確立したcorrection familyである。
  - `K0002`: ある分析設定でfull bias updateにvariance penaltyがあり、weighted correctionを動機付ける。
  - `K0009`: operating conditionが大きく変わらない場合、output calibrationはself-adjustmentよりsimple / lower-costとされる。
  - `K0011`: method selectionはresidual structure、measurement条件、outlier、operating-condition changeに依存し、universal numerical choiceを支持しない。
- finding:
  - Working Answer / J0002は「第一段としてweighted/tuned bias correctionから検証するのが妥当」と一般的なdefault recommendationとして読める。
  - selected Evidenceはbias correctionの存在、特定条件でのsimplicity、full updateのvariance trade-offを支持するが、5 familyを横断してweighted biasを常にfirst choiceとする比較Evidenceはない。
  - target-process dataも与えられていない。
- impact:
  - Methodological Working Answerのmethod-selection recommendationが、Evidenceが支持する条件付き主張より強くなる。
- repair direction:
  - 「比較的stableなoperating conditionで、residualが主にslow biasとして見える場合のcandidate baseline」等へ条件付けする。
  - またはcross-family comparison / target-process Evidenceを追加し、`20_synthesis` へmethod-selection basisを明示してからAnalysisを更新する。

### F-02 — rollback policyがSynthesisへtraceできない

- severity: **Minor**
- target: `J0006`
- evidence:
  - `J0006` は `K0002 / K0005 / K0011` を参照する。
  - これらはvariance / noise trade-off、residual-model limitation、method selection dependenceをsupportする。
- finding:
  - 「補正後performance悪化時にbase predictionへrollbackできるよう独立運用する」という運用policy自体は、参照Knowledge Unitに記録されていない。
- impact:
  - prudent engineering guidanceとEvidence-supported conclusionの境界が曖昧になる。
- repair direction:
  - proposal / implementation safeguardとして明示的にラベル付けするか、supporting Evidenceを追加してSynthesisへ上げる。

### F-03 — same holdout / rolling evaluationという比較設計を一般化している

- severity: **Minor**
- target: `J0007`
- evidence:
  - `K0011` はprocess-independent choiceを支持しない。
  - residual predictorに関する `E0013 / K0005` はheld-out validationの必要性をsupportする。
- finding:
  - 「複数補正方式を同一holdout/rolling evaluation条件で比較する」という具体的比較protocolは、全family共通のEvidence-supported contractとしてSynthesisに存在しない。
- impact:
  - sensible methodology proposalがcanonical Evidence resultと混同される。
- repair direction:
  - target-process evaluation proposalとして明示するか、cross-family evaluation designをsupportするEvidenceを追加する。

## 5. Checks with no material finding

今回のscopeでは次を確認した。

- `30_analysis` judgmentは `K####` referenceを持ち、raw Evidenceを直接referenceして `20_synthesis` をbypassしていない。
- `20_synthesis` はbias variance trade-off、stationarity / outlier limitation、process-domain transfer limit等の主要qualificationを保持している。
- `30_analysis` はMethodological profileを使用し、limitations / unresolved questions / alternative interpretationを持つ。
- 5 familyのtaxonomyは「mutually exclusive formal taxonomy」ではなくengineering taxonomyとqualificationされている。
- Source / Evidence Note provenanceから `10_evidence` への明白なcontent mismatchは今回の17 item照合では観測しなかった。

これらは「全Sourceをsystematicに再査読した」ことを意味しない。

## 6. Review target / staleness evaluation

targetはInvestigation ID + commit SHA + artifact blob SHAで一意に固定できた。

したがって、今回のpilotではTask 14 trigger 3の「review verdictのtargetを一意に特定できない事象」は観測しなかった。

将来target artifactが変わった場合、このpilot outcomeをnew artifactへ流用しない。新しいSHA / blobをfreezeして再Reviewする。

## 7. Repair / reReview lifecycle evaluation

findingは既存invalidation ruleへmappingできる。

- F-01 / F-02 / F-03は主として `30_analysis` findingであり、未accepted InvestigationならAnalysis stageからrepair / revalidate可能。
- Evidence / Synthesisを追加変更するrepairを選ぶ場合、`20_synthesis` または `10_evidence` の変更に応じてdownstreamをinvalidateする。
- frozen `00_context` のsemantic conditionを変える必要がある場合はnew Investigation。
- 既にacceptedされたInvestigationをsubstantively修正する必要がある場合は、`0002_investigation_versioning.md` を優先し、historical accepted artifactをin-place rewriteしない。

Notion RQにlegacy `Working Answer` propertyが存在することだけでは、現行 `# Working Answer` body projection contract上のCOMPLETE / accepted stateを証明しないため、このpilotではaccepted statusを推測していない。

repair後のartifactは別targetとしてreReviewする。このモデルは現行lifecycleと衝突しない。

## 8. Decision

pilotは、Semantic Reviewがdeterministic validatorでは検出しないsupport-boundary / recommendation-strengthの問題を発見し得ることを示した。

一方、今回観測したのは1 InvestigationにおけるModerate 1件 + Minor 2件であり、以下は観測していない。

- Major semantic errorの反復
- target SHAを一意に固定できないfailure
- concurrent reviewer / editorによる運用不安定
- stale Working Answer stateの反復
- regulated / high-stakes process requirement

したがってBKL-0021のdecisionは次とする。

> **Workflow 20をoptional independent Semantic Reviewとしてcanonicalizeする。ただしWorkflow 00のdefault COMPLETE gateにはせず、Review Seq / persistent Review JSON / dedicated schema / writer / SHA Control Planeはdeferを継続する。**

Task 14をmandatory Review導入の意味ではsupersedeしない。ただし「Review workflow自体を未導入」の状態から「optional Workflow 20 contractは存在する」状態へamendする。

## 9. Follow-up trigger

次のいずれかが観測された場合、mandatory gateまたはpersistent Review infrastructureを再評価する。

1. deterministic PASS後にMajor / materially consequential semantic findingが反復する。
2. optional Reviewを反復運用し、Review history / Seq / machine-readable finding storageが実務上必要になる。
3. review targetとcurrent artifactのstalenessを人手で管理できなくなる。
4. multiple actor / reviewer concurrencyでoptimistic concurrencyだけでは不十分になる。
5. regulated / high-stakes用途でindependent review evidenceの保存がprocess requirementになる。
