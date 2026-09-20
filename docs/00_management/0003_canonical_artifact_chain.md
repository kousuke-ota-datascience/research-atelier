# Canonical Research Artifact Chain

## 目的

本書は、1 Investigationに対するcanonical artifact architectureを定義する。

chainは次のとおり。

`00_context -> 10_evidence -> 20_synthesis -> 30_analysis`

中心的な設計制約は、**evidence-faithful representation** と **RQ-specific judgment** を別artifactに分離することである。

これは、都市伝説workflowでSource / Content再構成とAnalysis codingを分離していた考え方を一般Researchへ拡張し、その前段に明示的なfrozen Investigation Contextを追加したものである。

## 1. Canonical directory layout

v2 Investigation `INV-000001` の例:

```text
investigations/
  INV-000001/
    00_context.json
    10_evidence.json
    20_synthesis.json
    30_analysis.json
```

この4 JSON fileが、そのInvestigationのcanonical research artifactである。

Markdown / HTML / report / dashboard / Notion projectionなどのderived outputは、別契約で明示されない限りcanonicalではない。

## 2. Global invariants

4 artifactはすべて同じ `investigation_id` と同じ `rq_id` を持たなければならない。v2では `investigation_id` から `rq_id` を導出しない。

downstream artifactは、upstream canonical artifactに存在しないSource Evidenceを新規導入してはならない。

実質的なanalysis statementは次のchainでtraceできなければならない。

`30_analysis judgment -> 20_synthesis knowledge unit -> 10_evidence evidence item -> Notion Source / Evidence Note provenance`

dependencyは一方向である。downstreamはupstreamを解釈してよいが、downstream conclusionへ合わせるためにupstreamを書き換えてはならない。

## 3. 00_context

### 責務

`00_context` は、何をどの条件でinvestigateするかをfreezeする。

そのInvestigationにおけるInvestigation Context baselineである。

### 記載する

- `investigation_id`
- `rq_id`
- frozen question wording snapshot
- Question Type
- Scope
- 判明している場合のSignificance
- investigation boundary
- inclusion / exclusion constraint
- 必要な場合のtemporal boundary / evidence cutoff
- research setupを規定する明示的assumption
- Schemaが要求するcontext freeze state / provenance

### 記載しない

- Source excerpt / Evidence Note本体
- Evidence由来claim
- Synthesis conclusion
- Evidence間のagreement / conflict判断
- Working Answer
- RQ-specificなconclusion strength
- Analysis段階で後付けした解釈

### Authority

このInvestigationのfrozen Investigation Contextについて、本fileを正本とする。

Notion RQの関連状態をsnapshotするが、後続のNotion編集はhistorical contextを変更しない。

## 4. 10_evidence

### 責務

`10_evidence` は、そのInvestigationで実際に用いるEvidenceの正確なsnapshotである。

Notion Sources / Evidence Notes全件のcopyではない。downstream artifactが使用を許される、選択済みfrozen Evidence setである。

### 記載する

各selected evidence itemについて:

- Investigation内で安定な `evidence_id`
- 利用可能な場合のNotion Evidence Note URL
- Source URL
- source-faithfulな抽出内容 / structured note
- page / section / timestamp等のsource locator
- original source recordへ戻れるprovenance
- 必要な場合のみ、Evidence contentを変えないselection metadata

### 記載しない

- referenced Source / Evidence Noteに存在しないfact
- cross-source Synthesis
- どのSourceが最終的に正しいかというadjudication
- Working Answer
- RQ-specific causal / explanatory conclusion
- hypothesisへ合わせるためのunsupported paraphrase

### Selectionはcontextual、contentはevidence-faithful

Evidence itemを採用する判断はInvestigation-specificである。

ただしitem contentはSource / Evidence Noteへ忠実でなければならない。選択したことは再解釈の許可を意味しない。

### Authority

reusable Source / Evidence Note catalog recordはNotionが正本である。

`10_evidence` は、このInvestigationで実際に使うfrozen setとそのfrozen representationの正本である。

## 5. 20_synthesis

### 責務

`20_synthesis` はEvidence snapshotをevidence-faithfulなknowledge structureへ変換する。

都市伝説workflowにおける `contents` layerを一般Researchへ拡張した位置付けである。

最終RQ answerへ直ちに潰さず、Evidenceを再利用・監査可能な形へ構造化する。

### 記載する

- 1件以上の `10_evidence` itemに支持されるknowledge unit
- normalizeしたproposition / observation
- knowledge unit間の明示的relation
- Evidence間agreement
- conflict / contradiction
- uncertainty / missing information
- Sourceが報告するcausal claim、mechanism、estimate、interpretation（Source claimであることを保持）
- Evidence boundary / condition
- 各knowledge unitからsupporting `evidence_id` へのlineage

### 記載しない

- final Working Answer
- ユーザーが何を信じるべきかという判断
- Source claimのfaithful representationではないRQ-specificなoverall causal conclusion
- `10_evidence` に存在しないEvidence
- conflictを消してしまう暗黙のadjudication
- 定義済みmethodなしに生成したconfidence値

### Evidence-faithfulの意味

knowledge unitは表現のnormalization、重複Evidenceの統合、relationの明示をしてよい。

ただしlinked Evidenceから再構成できないpropositionを追加してはならない。

Source間で不一致がある場合、`20_synthesis` は不一致を保持する。暗黙にwinnerを選ばない。

Evidence不足はuncertaintyとして残す。

## 6. 30_analysis

### 責務

`30_analysis` は、RQ-specificなanalysis judgmentが初めてcanonicalになるartifactである。

frozen Investigation Contextの下で、evidence-faithful Synthesisを解釈する。

### Direct input

- `00_context`
- `20_synthesis`

`10_evidence` はaudit / traceabilityのため参照可能だが、`30_analysis` のsubstantive claimは `20_synthesis` knowledge unitを介さなければならない。

### 記載する

- Working Answer
- RQ-specific interpretation
- Question Type-specific profile / judgment
- methodが定義される場合のanswer strength / limit
- alternative explanation / interpretation
- limitation
- unresolved question
- analytical inferenceとして明示したimplication
- 各substantive judgmentを支持する `knowledge_unit_id`

### 記載しない

- `10_evidence` にない新Evidence
- `20_synthesis` にない新fact
- lineageのないsource-faithful fact
- 架空のcertainty
- Analysisに埋め込んだhidden assumption

### Boundary rule

「Evidenceが直接・共同で何を述べていると表現できるか」に答えるものは `20_synthesis` に置く。

「このRQ / contextの下で、そのEvidence representationから何を結論するか」に答えるものは `30_analysis` に置く。

## 7. Dependency graph

```text
Notion RQ / Source / Evidence Note catalog
             |
             v
        00_context
             |
             v
        10_evidence
             |
             v
        20_synthesis
             |
             v
        30_analysis
```

AnalysisではQuestion Type、Scope、assumptionを明示するため、`30_analysis` は `00_context` も直接読む。

logical dependency:

- `10_evidence <- 00_context`
- `20_synthesis <- 10_evidence`
- `30_analysis <- 20_synthesis + 00_context`

## 8. Invalidation rule

invalidationとは、変更されたupstreamに対して再生成または再評価されるまで、downstream artifactをvalidated / currentとして扱えない状態をいう。

### 00_context変更

freeze前にcontext-defining fieldを変更した場合:

- 同一draft Investigationを更新してよい
- 既作成の `10_evidence`、`20_synthesis`、`30_analysis` はinvalid

freeze後のcontext-defining changeは `0002_investigation_versioning.md` に従い新しいInvestigationを作る。

### 10_evidence変更

Evidence snapshotの実質的な追加・削除・置換・content変更は以下をinvalidateする。

- `20_synthesis`
- `30_analysis`

Evidence identity / contentを変えないformat / provenance表記変更はsemantic invalidationを要求しないが、deterministic validationは再度PASSさせる。

### 20_synthesis変更

knowledge unitまたはrelationの実質的変更は `30_analysis` をinvalidateする。

serializationのみの非意味的変更はsemantic re-analysisを要求しない。

### 30_analysis変更

`30_analysis` 変更はupstreamをinvalidateしない。

ただし `30_analysis` 自身は再validation / reviewする。

## 9. Invalidation matrix

| Changed artifact | 00_context | 10_evidence | 20_synthesis | 30_analysis |
| --- | --- | --- | --- | --- |
| 00_context | self | INVALID | INVALID | INVALID |
| 10_evidence | unchanged | self | INVALID | INVALID |
| 20_synthesis | unchanged | unchanged | self | INVALID |
| 30_analysis | unchanged | unchanged | unchanged | self |

`INVALID` は「rebuildまたはrevalidationされるまでcurrent / acceptedとして扱わない」を意味する。

## 10. No-bypass rule

canonical processingでは以下を禁止する。

- Notion Evidence Noteから `10_evidence` / `20_synthesis` を経由せず `30_analysis` へ入れる
- external Sourceを `10_evidence` に含めず `20_synthesis` へ入れる
- external Sourceから直接 `30_analysis` を作る
- Working Answerを `20_synthesis` へ書く
- downstream conclusionを正当化するためanalytical judgmentを `10_evidence` へ混入する

このruleによりauditabilityを保つ。

## 11. 最小lineage identifiers

v2 Schemaは少なくとも以下を扱う。

- 全artifactの `investigation_id`
- 各 `10_evidence` itemの `evidence_id`
- 各 `20_synthesis` unitの `knowledge_unit_id`
- knowledge unitからEvidenceへの `evidence_refs`
- analytical judgmentからSynthesis unitへの `knowledge_unit_refs`

正確なfield contractは `schemas/v1` を正とする。

## 12. 設計上の帰結

4 artifactは次の4つの問いを意図的に分離する。

1. `00_context`: 何を調査しているのか。
2. `10_evidence`: どのEvidenceを使うのか。
3. `20_synthesis`: agreement / conflict / uncertaintyを含め、そのEvidenceを何と言っているものとして表現できるか。
4. `30_analysis`: このRQ / contextの下で何を結論するか。

Working Answerはstage 30のみに存在する。


## 13. Legacy v1 compatibility

既存 `investigations/RQ-NNNN-vVVV/` はhistorical artifactとしてそのまま保持する。

- legacy artifactは `schemas/v1` でvalidationする。
- 新規artifactは `INV-NNNNNN` と `schemas/v2` を使用する。
- legacy directoryをv2へrename / rewriteしない。
