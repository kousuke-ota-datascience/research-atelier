# Workflow 10 — 1 InvestigationのResearch実行

## 0. 位置付け

本Workflowは、**accepted Research Questionに紐づく採番済みInvestigation**について、frozen Investigation Contextから `30_analysis` のdeterministic validationまでを構築するcanonical execution procedureである。Research Questionのsemantic formulation / acceptanceは本Workflowの責務外である。

本書が定義するのは、**実行順序と意味論上の作成規則**である。

JSON field、required、enum、reference format等の構造は再定義しない。新規canonical Investigationは `schemas/v2`、既存legacy Investigationは `schemas/v1` を正とする。

deterministic checkは以下へ委譲する。

`python -m research_atelier.validation.validate_investigation <Investigation_ID> --through 00|10|20|30`

semantic constructionでは、Human / Researcherがresearch intentとsemantic commitmentsを所有し、LLMはwording整理、候補提示、artifact materialization、Synthesis / Analysis作成を支援する。LLMは未確認のsemantic conditionを勝手に確定しない。

独立Semantic Reviewは `0020_semantic_review.md` のWorkflow 20が担う。Workflow 10はWorkflow 20を暗黙起動せず、Review finding / verdictを生成する責務を持たない。

## 1. Input / output

### Input

- 採番済みの `Investigation_ID` 1件。v2例: `INV-000001`
- 対応するNotion Research Question
- 対応するNotion Investigations DB row（newではWorkflow 00が作成、resumeでは既存rowをreuse）
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

目的は、frozen Investigation Contextに関連するcandidate Sourceを探索すること。

Source discoveryではNotion Sources / Evidence Notesへreusable recordを追加・refineしてよいが、analytical conclusionを直接作らない。

Evidence classに応じて、primary evidence、original data、official specification、original paperなど、問いを直接規定・報告するSourceを優先する。

high-authority Sourceが見つからない場合、その不在を隠さず、lower-quality Evidenceを暗黙に格上げしない。

### Evidence meaning

Research AtelierにおけるEvidenceは、LLMが「根拠」として生成した文章ではない。

Evidenceとは、**Sourceへtrace可能なsource-faithful observation / claim / result / method / definitionをcaptureし、必要なprovenanceを保持したもの**である。

- Sourceに存在しないclaimをEvidenceとして生成しない。
- analyst inferenceやcross-source interpretationをEvidence layerへ混入しない。
- Notion Evidence Noteを経由する場合、そのSource relationとlocation / quote等のprovenanceを保持する。
- direct source observationを使う場合も、後からSourceへ戻れるlocatorを保持する。

### Evidence selection

目的は、このInvestigationへ含めるsource-faithful Evidence Note / direct source observationを選択すること。

selectionはRQ / context-specificだが、desired answerへ合わせてEvidence contentを書き換えてはならない。

`10_evidence` はselected Evidenceとprovenanceだけをfreezeし、第二のbibliographic databaseにはしない。

### Synthesis

目的は、`10_evidence` からEvidence-faithful knowledge representationを構築すること。

wording normalization、Evidence grouping、agreement / conflict / uncertaintyの明示、relationの構造化を行ってよい。

ただしconflictを黙ってadjudicateしたり、final Working Answerを導入してはならない。

### Analysis

目的は、accepted RQとfrozen Investigation Contextに照らして `20_synthesis` を解釈すること。

`0009_analysis_profiles.md` で定義したQuestion Type profileを使用する。

RQ-specific judgmentとWorking Answerが初めてcanonicalになるstageである。

## 3. 実行手順

### Step 0 — Preflight

1. 対象Research Questionがhumanによって意味を定義・採択済みであり、「このRQを調査する」というresearch intentが成立していることを確認する。未採択の会話上の問いをWorkflow 10自身がcanonical RQとして生成しない。
2. 対象InvestigationのNotion Investigations rowが存在し、new / resumeのregistry contractをWorkflow 00が満たしていることを確認する。既存Git Investigationでrowが欠落している場合はWorkflow 00のcontrolled backfillを先に行う。
3. v2新規executionではInvestigation IDが `INV-NNNNNN` に従うことを確認する。既存v1 executionは `RQ-NNNN-vVVV` をlegacyとして維持する。
4. 対象Research Questionの `rq_id` を解決する。
5. v2ではInvestigation ID自体からRQを推定せず、Notion relationと `00_context.rq_id` でexactly one RQへbindする。
6. 同じInvestigation IDがmaterially異なるexecutionへ既に使われていないことを確認する。
7. authority、identity/lifecycle、artifact-chain、projection、profile contractを読む。
8. 既存Investigation directoryがある場合、current artifact stageを確認してから書き込みを始める。

identity / RQ bindingがambiguousなら停止する。

### Step 1 — `00_context` の構築とfreeze

1. 対象Investigation IDに対応するNotion Investigations rowをexactly one解決し、`Research Question` relationが対象RQと一致することを確認する。duplicate / ambiguousなら停止する。
2. Research Questions DBからprojection contractで指定されたRQ-level field（RQ ID、page URL、Question、optional Significance）をreadする。
3. Investigations DB rowからQuestion Type / Scope / Include / Exclude / Evidence Cutoff / Assumptionsをreadする。
4. unknownなScope / Significance / profile-relevant contextはnullまたは省略とし、defaultを捏造しない。
5. freeze前はNotion Investigations rowをmutable Context input authorityとして、intended research boundaryが十分明確になるまでdraftをrefineする。draft `00_context` を一時materializeしても独立authorityにしない。
6. RQ-level fieldとInvestigation rowをprojection contractに従って `00_context` へmaterializeし、`context_state = frozen` と `frozen_at` を設定する。
7. 以下を実行する。

```bash
python -m research_atelier.validation.validate_investigation <ID> --through 00
```

8. FAIL / ERRORでは次へ進まない。
9. `00_context.json` をcontext baselineとしてcommitする。
10. commit後はGit `00_context` を当該Investigation Contextのcanonical authorityとする。Notion rowはoperational / derived representationとなり、その差分からhistorical `00_context` を書き換えない。

以降、context-defining semantic changeには `0002_investigation_versioning.md` のlifecycle ruleを適用し、freeze後は新しいInvestigationを作る。

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

accepted Investigationでは、lifecycle contractが新しいInvestigationを要求するchangeをhistorical artifactへ上書きしない。

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
- Working AnswerからAnalysis / Judgment、Knowledge Unit、Evidence、Evidence Note、Sourceへ遡れるlineageが保たれている

accepted Working AnswerのNotion projectionはprojection contractとorchestration workflowの責務であり、artifact construction自体には含めない。

Workflow 20は本completion conditionのdefault必須要件ではない。through-30 PASSはSemantic Reviewの開始前提にはなり得るが、deterministic PASSをsemantic correctnessの証明とはみなさない。Human / Workflow 00がacceptance前のReviewを明示的prerequisiteとして要求した場合だけ、そのReview handoffを完了してからfinal acceptanceへ進む。

## 9. Execution boundary invariant

Workflow 10は**Investigation execution**のworkflowであり、Research Questionを作るworkflowではない。

対象のaccepted RQに対して外部Sourceを探索しsubstantive conclusionを生成するなら、Workflow 00からhandoffされたInvestigationとして本Workflowを実行する。chat上のad hoc Web回答だけで、Source / Evidence capture、`10_evidence`、`20_synthesis`、`30_analysis` を省略してcanonical research resultとみなしてはならない。

そのようなad hoc回答はResearch Atelier上ではworkflow incomplete / non-canonicalであり、accepted Working Answer projectionのsourceにならない。


## 10. Workflow 20 findingからのrepair

Workflow 20でcanonical Review JSONにFindingが確定した場合、reviewer自身がcanonical artifactを直接修正せず、Findingの `repair_direction` をWorkflow 00 / 10へhandoffする。

- `affected_layer = 10_evidence` -> Evidence stageからrepairし、20 / 30をinvalidateする。
- `affected_layer = 20_synthesis` -> Synthesis stageからrepairし、30をinvalidateする。
- `affected_layer = 30_analysis` -> Analysis stageからrepair / revalidateする。
- `affected_layer = 00_context` -> frozen context変更なので原則 `new_investigation`。
- `repair_direction.mode = new_investigation` -> same Investigationをrepairしない。

same-Investigation repairを開始する直前、Workflow 00はReview reconcilerへexplicit `repair_started` eventを渡す。Review JSONの存在だけで `要修正 -> 再作業中` を推測しない。

dependency invalidationは既存contractを維持する。

```text
10_evidence change -> invalidate 20_synthesis + 30_analysis
20_synthesis change -> invalidate 30_analysis
30_analysis change -> 30 only
```

repair artifact commit後はold Reviewのfrozen blob SHAとcurrent chainが不一致になるため、reconcilerは `再レビュー待` をderiveする。old Review outcomeをnew targetへ流用せず、Workflow 20でnext Review SeqをallocateしてreReviewする。

accepted Investigationのsubstantive repairではhistorical accepted resultをin-place rewriteせず、`0002_investigation_versioning.md` を優先する。

## 11. v1 legacy handling

既存 `RQ-NNNN-vVVV` directoryを実行・再検証する場合は `schemas/v1` を使用し、identityをin-place migrationしない。新規Investigationは `INV-NNNNNN` + `schema_version = 2.0.0` を使用する。
