# Research architecture / authority boundary

## 目的

本書は、research-atelier における責務と authority boundary の正本仕様である。

同じ情報を複数箇所で独立管理しないため、capture、frozen research artifact、意味論的構築、構造契約、deterministic enforcement を分離する。

## 文書言語

正本ドキュメントの基本言語は日本語とする。

ただし、以下は理解・契約上の明確性を優先し、必要に応じて原語のまま使用する。

- JSON field名
- path / CLI / identifier
- JSON Schema用語
- Research Question / Investigation / Working Answer / Question Type / lineage など、英語のままの方が参照関係を保ちやすい技術用語
- 規格・ライブラリ・製品・固有名詞

## Authority model

| 対象 | System / actor | 責務 | Authority |
| --- | --- | --- | --- |
| Research intent / semantic commitment | Human / Researcher | Research Questionの意味の定義・採択、調査実行の意図、Scope / assumptions / cutoff等の意味論的条件の決定・確認 | 「何を・どの意味で調べるか」のdecision authority |
| Discovery、capture、reusable catalog | Notion | Research Topics、Research Questions、Sources、Evidence Notes、task state | mutableなreusable catalog record / operational task stateの正本 |
| Investigation operational representation | Notion Investigations DB | 1 Investigation = 1 row、explicit RQ binding、freeze前のQuestion Type / Scope / Include / Exclude / Evidence Cutoff / Assumptions、Review current pointer | freeze前のInvestigation Context inputとmutable operational stateの正本。freeze後のContext semantic authorityはGit `00_context`へ移る |
| Frozen Investigation artifact | Git JSON | Investigation Context、Evidence snapshot、Synthesis、Analysis | 特定Investigationの正本 |
| Semantic assistance / materialization | LLM | RQ wording整理、条件候補提示、Investigation Context / Evidence / Synthesis / Analysisのmaterialization支援 | semantic proposalを作れるが、RQのsemantic ownership、research intent、未確認conditionを単独で確定しない |
| Investigation orchestration | Workflow 00 / deterministic system | accepted RQまたは既存Investigationを入口として、resume / new判定、INV ID採番、lifecycle / invalidation、accepted result projectionを管理 | execution identity / lifecycle / orchestrationのauthority。RQ semantic meaningのauthorityは持たない |
| Investigation execution | Workflow 10 | frozen Investigation Contextの下でSource discovery、Evidence capture / selection、Synthesis、Analysisを順序立てて実行 | canonical execution procedureのauthority。Research Questionの作成・採択は責務外 |
| Independent semantic assessment | Workflow 20 | committed Investigation artifactについてEvidence-faithfulness、Synthesisのsupport境界、Question Type固有analysis、Working Answer / limitation等を独立評価し、実行時はcanonical Review JSONを永続化 | optional semantic assessmentのprocedure authority。Review実行の有無はoptionalだが、実行したReviewのFinding / Verdict / target freezeはGit Review JSONがauthority |
| 構造契約 | JSON Schema | 許可構造、required、type、enum、conditional structure | artifact structureの正本契約 |
| Deterministic enforcement | Python | schema、reference、ID、version/path、その他機械判定可能なinvariantの検査 | machine-checkable ruleの実行正本 |

## Domain identity model

v2のcanonical domain modelは次のとおり。

```text
Research Question (RQ)
  1
  |
  | 0..*
  v
Investigation (INV)
  |
  +-- 00_context = frozen Investigation Context
  +-- 10_evidence
  +-- 20_synthesis
  +-- 30_analysis
```

- **Research Question** は「何を問うか」の長期的semantic identityであり、Notion catalogがcurrent stateの正本である。
- **Investigation** は、1つのRQを特定のexecution conditionで実行する独立identityである。v2のIDは `INV-NNNNNN` とし、RQ IDをID文字列へ埋め込まない。
- **Investigation Context** はInvestigation固有のimmutable execution inputであり、`00_context.json` がfreeze後の正本である。
- **Research Context** はproblem / decision context / hypothesis / domain framing等の上流概念を指す一般語としてのみ使用する。v2では独立identity、独立version、canonical DBを持つfirst-class entityにはしない。
- 将来、同一framingを複数RQ / Investigationから独立に再利用・versioningする実需要が確認された場合に限り、Research Contextを別entityとして追加する。その場合もInvestigation Contextと混同しない。

canonicalに固定するcardinalityは **RQ 1 : Investigation 0..*** であり、各Investigationはexactly one RQを参照する。

## Human / workflow responsibility boundary

Research Atelierは、Research Questionを生成するworkflowではない。canonical research workflowは、**人間が意味を定義し採択したResearch Question**、または既存Investigation IDを外部入力として開始する。

基本原則は次のとおり。

> **Human owns research intent and semantic commitments. Workflow owns Investigation lifecycle and identity allocation.**

- Human / ResearcherはResearch Questionのsemantic identity、調査するというintent、Scope / assumption / cutoff等の意味論的条件を決定・確認する。
- LLMはQuestion wordingの整理、候補提示、artifact materializationを支援できるが、human-ownedなsemantic commitmentを暗黙に確定しない。
- Workflow 00はaccepted RQからInvestigationをorchestrateし、resume / new、ID、lifecycle、invalidation、final projectionを管理する。
- Workflow 10はInvestigation executionを担当し、Research Questionの作成・採択を行わない。
- Workflow 20は、明示的に起動された場合にInvestigationのsemantic correctnessを独立評価するoptional workflowである。findingは記録するが、Research Questionを再定義せず、reviewer自身がcanonical artifactを直接repairしない。
- deterministic systemはmachine-checkableなstate / identity / validationを管理し、semantic research intentを推測しない。

BKL-0021で確定した「Workflow 20はdefault completion gateにしない」というdecisionは維持する。BKL-0027以降は、**Review実行自体はoptionalだが、実行したReviewのpersistent JSON / history / current-state reconciliationはmandatory**とする。Review未実施だけを理由にVALIDATED / COMPLETEを阻害しない。

Task 17が定義するのはRQ / Investigation / Investigation Contextの**domain model**であり、本節が定義するのはactor responsibility / workflow entrance / execution authorityである。両者を混同しない。

## Canonical research execution invariant

対象となるaccepted Research Questionが存在し、外部Sourceを探索してsubstantive conclusionを生成する場合、そのresearch executionはWorkflow 00を入口としてWorkflow 10のcanonical chainを経由しなければならない。

```text
accepted Research Question
        |
        v
Workflow 00
        |
        v
Investigation Context freeze
        |
        v
Source discovery / Evidence capture
        |
        v
10_evidence
        |
        v
20_synthesis
        |
        v
30_analysis
        |
        v
accepted Working Answer projection
```

chat上のad hoc Web searchやcitation付き回答だけで、Sources / Evidence Notes / `10_evidence` / `20_synthesis` / `30_analysis` を経由せずにcanonical research resultを成立させてはならない。そのような回答は参考情報にはなり得るが、Research Atelier上は**workflow incomplete / non-canonical**として扱う。

## Evidence and lineage invariant

Research AtelierにおけるEvidenceとは、LLMが根拠らしい文章を生成することではない。**Sourceへtrace可能なsource-faithful observation / claimをcaptureし、必要なprovenanceを保持したもの**である。

canonical resultは少なくとも次のlineageを辿れることを要求する。

```text
Working Answer
  -> Judgment / Analysis
  -> Knowledge Unit
  -> Evidence
  -> Evidence Note
  -> Source
```

途中段階をLLMの非追跡な要約で代替してはならない。Sourceの内容、workflowによるSynthesis、RQ-specific analytical judgmentを区別する。

## Single-authority rule

各情報クラスは、必ず1つだけcanonical authorityを持つ。

derived copyはprojection、snapshot、cache、renderingとしてのみ存在できる。derived representationを独立編集可能な第二の正本にしてはならない。

表現同士が矛盾した場合は、本書で定義したcanonical authorityを優先する。非正本側は再生成・reconcile・invalidateする。

## 情報クラス別の正本

### Notion-authoritative

- Research Topic catalogとmutable metadata
- Research Question catalogとmutable RQ-level metadata
- Investigation rowのidentity / explicit RQ binding、およびfreeze前のQuestion Type / Scope / Include / Exclude / Evidence Cutoff / Assumptions
- Investigation Reviewのcurrent operational pointer（Review Status / Latest Review Seq）
- Source identityとbibliographic metadata
- source-faithfulなreusable Evidence Note
- Backlog / workflow statusなどのoperational current state

### Git artifact-authoritative

1つのfrozen Investigationについて:

- Investigation Context
- そのversionで選択したEvidence snapshot
- evidence-faithful Synthesis
- RQ-specific AnalysisとWorking Answer
- canonical artifact内のlineage / version identifiers
- Workflow 20を実行した場合のappend-only Semantic Review history
  - `(Investigation ID, Review Seq)` identity
  - frozen target commit / artifact blob SHA
  - transition別semantic assessment
  - Findings / repair direction
  - deterministic Verdict

### Contract-authoritative

- JSON Schemaはartifact shapeの正本である。
- JSON Schemaだけでは表現しにくいcross-artifact constraintはPython validationを正本実装とする。

### 非正本のcomputational actor

- LLM outputは、canonical artifactへ書き込まれvalidationされるまではsemantic proposalである。
- rendered document、summary、dashboard、NotionへのGit結果projectionは、別仕様で昇格されない限りderived viewである。

## Write-direction constraints

1. freeze前はNotion Research QuestionのQuestion / provenance等とNotion Investigations rowのInvestigation-specific conditionを、Git `00_context` へsnapshotしてよい。
2. `00_context` がfreezeされcommitされた後、そのInvestigation ContextのauthorityはGitへ移る。Notion Investigations rowを独立した第二のsemantic authorityとして編集してはならない。
3. Git canonical analysisはNotionのoperational current stateへprojectionしてよいが、別のsync contractがauthority transferを明示しない限りderivedである。
4. projection / backfillにはsource Investigation identityを識別できるprovenanceを残す。
5. 既存InvestigationのNotion rowが欠落している場合、frozen Git `00_context` をauthorityとしてoperational rowをbackfillしてよい。current RQ metadataからhistorical conditionを逆算しない。
6. 同一fieldをNotionとGitの双方でauthoritativeに手動管理してはならない。
7. upstream canonical artifactが変更された場合、依存するdownstream artifactは再validationまたは再生成されるまでinvalidとする。
8. Workflow 20 Review content / Findings / VerdictはGit Review JSONがauthorityであり、Notion Investigations DBには `Review Status / Latest Review Seq` というderived current pointerだけを保持する。
9. Review Status mutationは `src/research_atelier/reviewing/reconcile.py` のdeterministic planを介し、Workflow 20やconnectorが独自に書き換えない。

## docs/98_reusable_artifact の位置付け

`docs/98_reusable_artifact` は、旧・都市伝説workflowから継承したreference / provenance materialである。

設計参照として保持するが、新Research workflowの正本仕様ではない。

新Research仕様は主として `docs/00_management`、`docs/10_workflows`、Research用schema / implementationへ置く。

## 設計上の帰結

Research workflowは次の分離を基本とする。

`Evidence -> evidence-faithful structured representation -> analytical judgment`

実装責務は次のとおり。

```text
Human        = research intent / semantic commitments
Notion       = operational state / reusable catalog
Workflow 00  = Investigation orchestration / lifecycle / projection
Workflow 10  = canonical Investigation execution procedure
Workflow 20  = optional independent semantic assessment
Git JSON     = frozen canonical artifact
LLM          = semantic assistance / materialization
JSON Schema  = structure contract
Python       = deterministic enforcement
```

このboundaryを、Investigation identity/lifecycle、canonical artifact、validation、Notion/Git projectionの前提とする。
