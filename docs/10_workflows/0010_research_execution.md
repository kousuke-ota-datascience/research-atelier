# Workflow 10 — 1 InvestigationのResearch実行

## 0. 位置付け

本Workflowは、frozen contextから `30_analysis` のdeterministic validationまで、1つのResearch Investigationを構築するcanonical execution procedureである。

本書が定義するのは、**実行順序と意味論上の作成規則**である。

JSON field、required、enum、reference format等の構造は再定義しない。構造契約は `schemas/v1` を正とする。

deterministic checkは以下へ委譲する。

`python -m research_atelier.validation.validate_investigation <Investigation_ID> --through 00|10|20|30`

semantic constructionはLLM / researcherの責務とする。

## 1. Input / output

### Input

- 採番済みの `Investigation_ID` 1件。例: `RQ-0007-v001`
- 対応するNotion Research Question
- reusable Notion Sources / Evidence Notes catalogへのaccess

### Canonical output

```text
investigations/<Investigation_ID>/
  00_context.json
  10_evidence.json
  20_synthesis.json
  30_analysis.json
```

## 2. 責務境界

### Source discovery

目的は、frozen Research Contextに関連するcandidate Sourceを探索すること。

Source discoveryではNotion Sources / Evidence Notesへreusable recordを追加・refineしてよいが、analytical conclusionを直接作らない。

Evidence classに応じて、primary evidence、original data、official specification、original paperなど、問いを直接規定・報告するSourceを優先する。

high-authority Sourceが見つからない場合、その不在を隠さず、lower-quality Evidenceを暗黙に格上げしない。

### Evidence selection

目的は、このInvestigationへ含めるsource-faithful Evidence Note / direct source observationを選択すること。

selectionはRQ / context-specificだが、desired answerへ合わせてEvidence contentを書き換えてはならない。

`10_evidence` はselected Evidenceとprovenanceだけをfreezeし、第二のbibliographic databaseにはしない。

### Synthesis

目的は、`10_evidence` からEvidence-faithful knowledge representationを構築すること。

wording normalization、Evidence grouping、agreement / conflict / uncertaintyの明示、relationの構造化を行ってよい。

ただしconflictを黙ってadjudicateしたり、final Working Answerを導入してはならない。

### Analysis

目的は、frozen RQ / contextに照らして `20_synthesis` を解釈すること。

`0009_analysis_profiles.md` で定義したQuestion Type profileを使用する。

RQ-specific judgmentとWorking Answerが初めてcanonicalになるstageである。

## 3. 実行手順

### Step 0 — Preflight

1. Investigation prefixに対応するRQを解決する。
2. Investigation IDが `RQ-NNNN-vVVV` に従うことを確認する。
3. 同じversionがmaterially異なるfrozen contextへ既に使われていないことを確認する。
4. authority、versioning、artifact-chain、projection、profile contractを読む。
5. 既存Investigation directoryがある場合、current artifact stageを確認してから書き込みを始める。

identity / version ownershipがambiguousなら停止する。

### Step 1 — `00_context` の構築とfreeze

1. projection contractで指定されたNotion RQ fieldをsnapshotする。
2. 判明しているInvestigation-specific boundary / assumptionを追加する。
3. unknownなScope / Significance / profile-relevant contextはnullまたは省略とし、defaultを捏造しない。
4. freeze前に、intended research boundaryが十分明確になるまでdraftをrefineする。
5. `context_state = frozen` と `frozen_at` を設定する。
6. 以下を実行する。

```bash
python -m research_atelier.validation.validate_investigation <ID> --through 00
```

7. FAIL / ERRORでは次へ進まない。
8. `00_context.json` をcontext baselineとしてcommitする。

以降、context-defining semantic changeには `0002_investigation_versioning.md` のversioning ruleを適用する。

### Step 2 — Source探索とreusable Evidence Note capture

1. frozen question、Scope、investigation boundaryに関連するEvidenceを探索する。
2. ad hoc bibliographyをGitへ直接埋め込まず、reusable Source recordをNotionへ登録する。
3. 必要に応じてLocation / quoteを付け、source-faithful Evidence Noteをcaptureする。
4. contradictory Evidenceやnull resultも追跡し、confirming materialだけを選ばない。
5. Source claimとanalyst inferenceを区別する。
6. scoped questionへ答えるために十分なEvidenceが集まった場合、または追加探索のexpected information gainがresource costに見合わなくなった場合に探索を停止する。
7. 重要なEvidence gapは推測で埋めず明示する。

Source discoveryはiterativeである。Investigation accept前に新しいrelevant Sourceが見つかった場合、このStepへ戻ってよい。

### Step 3 — `10_evidence` の選択とfreeze

1. このInvestigationで実際に使用するEvidenceを選択する。
2. Investigation-localな `E####` IDを付与する。
3. projection contractに従ってNotion Source / Evidence Note provenanceを保持する。
4. Sourceにあるuncertainty / qualificationを保持する。
5. cross-source Synthesis、causal judgment、Working Answerを追加しない。
6. through 10をvalidationする。
7. FAIL / ERRORでは次へ進まない。
8. `10_evidence.json` を独立commitする。

selected Evidence setが後からsubstantively変わった場合、`20_synthesis` と `30_analysis` はinvalidateする。

### Step 4 — `20_synthesis` の構築

1. `10_evidence` に存在するEvidenceだけを用いる。
2. stableな `K####` knowledge unitを作り、`evidence_refs` を付ける。
3. supportされる範囲でagreement、conflict、qualification、dependency、association、uncertaintyを表現する。
4. Source-reported explanationとworkflow自身のanalytical conclusionを区別する。
5. unresolved conflictを保持し、Sourceのwinnerを強制しない。
6. Working Answerを置かない。
7. through 20をvalidationする。
8. FAIL / ERRORでは次へ進まない。
9. `20_synthesis.json` を独立commitする。

Evidenceが変わった場合、Analysisへ進む前にSynthesisをrebuild / revalidateする。

### Step 5 — `30_analysis` の構築

1. frozen `00_context` とvalidated `20_synthesis` を読む。
2. `question_type` に対応するprofileを選択する。
3. known / applicableなprofile fieldだけを埋める。
4. RQ-specific judgment、limitation、alternative interpretation、unresolved question、Working Answerを作る。
5. schemaが要求するsubstantive judgmentは、1件以上の `K####` へtraceする。
6. raw Evidence referenceをanalysis judgmentへ直接入れてSynthesisをbypassしない。
7. Synthesisに表現されたfactと、新しいanalytical inferenceを区別する。
8. associationをcausationへ、predictive performanceをmechanismへ、conceptual coherenceをempirical supportへ変換しない。
9. through 30をvalidationする。
10. FAIL / ERRORでは次へ進まない。
11. `30_analysis.json` を独立commitする。

## 4. Evidence不足時のrule

Evidence不足は正当なresearch outcomeであり、fabricated completionは許されない。

support不能になった最も早いstageでsemantic constructionを停止する。

- contextがInvestigationを定義できるほど明確でない場合、freeze前で停止する。
- usable Evidenceを確立できない場合、`10_evidence` contentを捏造しない。
- Evidenceがknowledge unitをsupportしない場合、`20_synthesis` を捏造しない。
- Synthesisがsubstantive answerをsupportしない場合、そのanswerを推論しない。

「available Evidenceでは不十分である」こと自体が有用なresultである場合、Evidence search boundaryとrelevant gapが明示され、unsupported substantive conclusionを混入していない場合に限り、それを `30_analysis` Working Answerとしてよい。

## 5. Upstream change / invalidation handling

upstream canonical artifactを編集する前に、versioning ruleがin-place changeを許すか確認する。

まだacceptされていないInvestigation内では:

- `00_context` change -> 10 / 20 / 30をinvalidate
- `10_evidence` change -> 20 / 30をinvalidate
- `20_synthesis` change -> 30をinvalidate
- 30 change -> 30自身のみ再評価

accepted Investigationでは、versioning contractが新versionを要求するchangeをhistorical artifactへ上書きしない。

`INVALID` は、new upstream stateに対してreconstructまたは明示的にrevalidateされるまで、downstream artifactをcurrentとして扱えないことを意味する。

## 6. Deterministic validation rule

各stageではinternal validator functionではなくpublic CLIを実行する。

machine-readable result:

- `PASS`: deterministicなstructure / identity / reference ruleを満たす
- `FAIL`: artifact contentがdeterministic ruleに違反
- `ERROR`: validation infrastructure / schema configurationを信頼して実行できない

次canonical artifactへ進めるのはPASSのみ。

PASSはsemantic analysisがscientifically correctであることを意味しない。

## 7. Git rule

canonical artifact changeはartifact boundary単位でcommitする。

推奨順序:

1. validated `00_context`
2. validated `10_evidence`
3. validated `20_synthesis`
4. validated `30_analysis`

Investigation artifact確定commitへ、無関係なworkflow refactorを混在させない。

Git historyはprovenanceだが、research stateの正本はartifact contentとvalidation contractである。

## 8. Completion condition

Workflow 10は以下をすべて満たしたとき完了とする。

- `00_context` がfrozen
- selected `10_evidence` がsource-faithful
- `20_synthesis` がEvidence lineage、disagreement、uncertaintyを保持
- `30_analysis` が正しいQuestion Type profileを使用
- through 30 validationがPASS
- 4 artifactがcommit済み
- known upstream changeによってinvalidatedされたdownstream artifactが残っていない

accepted Working AnswerのNotion projectionはprojection contractとorchestration workflowの責務であり、artifact construction自体には含めない。
