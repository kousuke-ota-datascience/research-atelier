# Workflow 10 — 1 InvestigationのResearch実行

## 0. 位置付け

本Workflowは、1つのResearch Investigationについて、frozen contextから `30_analysis` のdeterministic validationまでを構築するcanonical execution procedureである。

本書が定義するのは**実行順序と意味論上の作成規則**である。

JSON field、required property、enum、reference formatは再定義しない。構造契約は `schemas/v1` を正とする。

deterministic checkは以下へ委譲する。

`python -m research_atelier.validation.validate_investigation <Investigation_ID> --through 00|10|20|30`

semantic constructionはLLM / researcherの責務である。

## 1. Input / output

### Input

- allocated `Investigation_ID` 1件。例: `RQ-0007-v001`
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

目的: frozen Research Contextに関係するcandidate Sourceを見つける。

Source discoveryではNotion Sources / Evidence Notesへreusable recordを追加・改善してよい。Analysis conclusionを直接作らない。

Evidence classとして適切な場合、一次資料、original data、official specification、original paperなど対象を直接規定・報告するSourceを優先する。

high-authority Sourceがない場合、その不在を隠さない。lower-quality Evidenceを暗黙に格上げしない。

### Evidence selection

目的: このInvestigationに含めるsource-faithful Evidence Note / direct source observationを選ぶ。

selectionはRQ / Context-specificである。desired answerへ合わせてEvidence contentを書き換えない。

`10_evidence` はselected Evidenceとprovenanceのみをfreezeし、第二のbibliographic DBにはしない。

### Synthesis

目的: `10_evidence` からevidence-faithful knowledge representationを作る。

wording normalization、Evidence grouping、agreement / conflict / uncertaintyの明示、relation構築は可能。

conflictを暗黙解消したりfinal Working Answerを混入してはならない。

### Analysis

目的: frozen RQ / Contextに対して `20_synthesis` を解釈する。

`0009_analysis_profiles.md` で定義したQuestion Type profileを使用する。

RQ-specific judgmentとWorking Answerがcanonicalになる最初のstageである。

## 3. 実行手順

### Step 0 — Preflight

1. Investigation prefixに対応するRQを解決する。
2. Investigation IDが `RQ-NNNN-vVVV` に従うことを確認する。
3. 同じversionが実質的に異なるfrozen contextへ既に使われていないことを確認する。
4. authority / versioning / artifact-chain / projection / profile contractをloadする。
5. Investigation directoryが存在する場合はcurrent artifact stageを確認する。

identity / version ownershipが曖昧なら停止する。

### Step 1 — `00_context` を構築・freeze

1. projection contractで指定したNotion RQ fieldをsnapshotする。
2. 判明しているInvestigation-specific boundary / assumptionを追加する。
3. unknown Scope / Significance / profile関連contextは省略または `null` とし、defaultを捏造しない。
4. freeze前にresearch boundaryを十分明示できるまでdraftを改善する。
5. `context_state = frozen`、`frozen_at` を設定する。
6. 実行する:

```bash
python -m research_atelier.validation.validate_investigation <ID> --through 00
```

7. FAIL / ERRORなら進まない。
8. `00_context.json` をcontext baselineとしてcommitする。

以後、context-defining semantic changeは `0002_investigation_versioning.md` に従う。

### Step 2 — Source探索 / reusable Evidence Note capture

1. frozen Question / Scope / investigation boundaryに関連するEvidenceを探索する。
2. ad hoc bibliographyをGitへ直接埋めず、reusable Source recordをNotionへ追加する。
3. 必要に応じてLocation / Direct Quoteを含むsource-faithful Evidence Noteを作る。
4. contradictory Evidence / null resultも追跡し、confirming materialだけを選ばない。
5. Source claimとanalyst inferenceを区別する。
6. scoped questionへ答えるのに十分なEvidenceが揃うか、expected information gain / resource constraint上これ以上の探索が正当化されなくなった時点で探索を止める。
7. 重要なEvidence gapは明示し、推測で埋めない。

Source discoveryはaccepted前ならiterativeでよい。

### Step 3 — `10_evidence` を選択・freeze

1. このInvestigationで実際に使うEvidenceを選ぶ。
2. Investigation-local `E####` IDを付ける。
3. projection contractに従いNotion Source / Evidence Note provenanceを保持する。
4. Sourceのuncertainty / qualificationを保持する。
5. cross-source Synthesis、causal judgment、Working Answerを入れない。
6. through 10でvalidationする。
7. FAIL / ERRORなら進まない。
8. `10_evidence.json` をartifact単位でcommitする。

後でEvidence setが実質的に変わった場合、`20_synthesis` と `30_analysis` はinvalidとなる。

### Step 4 — `20_synthesis` を構築

1. `10_evidence` 内Evidenceだけを使う。
2. stable `K####` knowledge unitを作り、`evidence_refs` を付ける。
3. supportedなagreement / conflict / qualification / dependency / association / uncertaintyを表現する。
4. Source-reported explanationとworkflow自身のanalytical conclusionを区別する。
5. unresolved conflictを保持し、無理にwinnerを決めない。
6. Working Answerを置かない。
7. through 20でvalidationする。
8. FAIL / ERRORなら進まない。
9. `20_synthesis.json` をartifact単位でcommitする。

Evidenceが変わったら、Analysis前にSynthesisを再構築または再validationする。

### Step 5 — `30_analysis` を構築

1. frozen `00_context` とvalidated `20_synthesis` を読む。
2. `question_type` に一致するprofileを選ぶ。
3. known / applicableなprofile fieldだけを埋める。
4. RQ-specific judgment、limitation、alternative、unresolved question、Working Answerを作る。
5. Schemaが要求するsubstantive judgmentは1つ以上の `K####` へtraceする。
6. raw Evidence referenceをAnalysis judgmentへ入れてSynthesisをbypassしない。
7. Synthesisに表現されたfactと新しいanalytical inferenceを区別する。
8. associationをcausationへ、predictive performanceをmechanismへ、conceptual coherenceをempirical supportへ変換しない。
9. through 30でvalidationする。
10. FAIL / ERRORなら進まない。
11. `30_analysis.json` をartifact単位でcommitする。

## 4. Evidence不足時のrule

Evidence不足はvalidなresearch outcomeである。fabricated completionは不可。

支持できなくなった最も早いstageでsemantic constructionを停止する。

- Contextを定義できない -> freeze前に停止
- usable Evidenceを確立できない -> `10_evidence` contentを捏造しない
- Evidenceがknowledge unitを支持しない -> `20_synthesis` を捏造しない
- Synthesisがsubstantive answerを支持しない -> 結論を推測しない

「available Evidenceでは不十分」が有用な結果の場合、Evidence search boundaryとrelevant gapが明示され、unsupported substantive conclusionを混入しないなら、`30_analysis` のWorking Answerとして記録してよい。

## 5. Upstream change / invalidation

upstream canonical artifactを変更する前に、versioning rule上in-place changeが許されるか確認する。

未accepted Investigation内では:

- `00_context` change -> 10, 20, 30 invalid
- `10_evidence` change -> 20, 30 invalid
- `20_synthesis` change -> 30 invalid
- 30 change -> 30自身のみ再評価

accepted Investigation後は、versioning contractが要求する変更をhistorical artifactへ上書きせず新Investigation versionへ送る。

invalidとは、downstream artifactが新upstreamに対してreconstructまたは明示的にrevalidateされるまでcurrentとして扱えないことを意味する。

## 6. Deterministic validation rule

各stageでinternal functionではなくpublic CLIを使う。

machine-readable result:

- `PASS`: deterministic structure / identity / reference ruleを通過
- `FAIL`: artifact contentがdeterministic rule違反
- `ERROR`: validation infrastructure / schema configurationを信頼して実行できない

次stageへ進めるのはPASSだけ。

PASSはsemantic Analysisの科学的正しさを意味しない。

## 7. Git rule

canonical artifact changeはartifact boundaryでcommitする。

推奨順序:

1. validated `00_context`
2. validated `10_evidence`
3. validated `20_synthesis`
4. validated `30_analysis`

Investigation artifact commitへ無関係なworkflow refactoringを混在させない。

Git historyはprovenanceであるが、research stateの正本はartifact contentとvalidation contractである。

## 8. Completion condition

Workflow 10の完了条件:

- `00_context` がfrozen
- selected `10_evidence` がsource-faithful
- `20_synthesis` がEvidence lineage / disagreement / uncertaintyを保持
- `30_analysis` が正しいQuestion Type profileを使用
- validation through 30がPASS
- 4 artifactがcommit済み
- known upstream changeによるinvalidated downstreamが残っていない

accepted Working AnswerのNotion projectionはartifact constructionではなくprojection contract / orchestration workflowの責務とする。
