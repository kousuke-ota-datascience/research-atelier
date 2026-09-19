# 0. ドキュメント情報

## 0.1. 位置付け

本書は、1つの `Entry_ID` を対象として、典拠調査から canonical artifact 作成、deterministic validation、Git確定、Review引渡し、Review返却後のCoder修正までを統括するCoder側オーケストレーションの正本である。

## 0.2. 設計原則

- Workflow 10は実行順序と意味論上の作成規則を定義する。
- canonical dataの構造契約はJSON Schemaを正とし、本書ではfield構造を再定義しない。
- 同一入力に対して機械的に判定できる検査はPythonへ委譲する。
- 独立した意味論的妥当性判定はWorkflow 20へ委譲する。
- control plane同期・更新はWorkflow 90へ一元化し、本書からNotionを直接更新しない。
- 外部入力は原則 `Entry_ID` のみとする。

# 1. 目的と責務

## 1.1. 目的

`Entry_ID` で指定された1件の伝承について、Evidenceを収集し、Contentを再構成し、Version Scopeを確定した上でD01〜D21を分析し、deterministic validationを通過したcanonical artifactをGitへ確定し、Review可能な状態まで進める。

## 1.2. 担う責務

- 対象Entryを確定する。
- 必要な典拠を探索し、Evidenceを収集する。
- `<Entry_ID>_00_sources.json` を作成・更新する。
- `00_sources.json` を根拠として `<Entry_ID>_10_contents.json` を作成・更新する。
- Content完成後にVersion Scopeを確定する。
- 作成後 `python -m src.validation.validate_entry <Entry_ID> --through 10` を実行し、00→10の構造・参照整合まで検証する。
- `10_contents.json` を根拠として `<Entry_ID>_20_analysis.json` を作成・更新する。
- 作成後 `python -m src.validation.validate_entry <Entry_ID> --through 20` を実行し、00→10→20全体とtaxonomyを検証する。
- 各canonical artifactについてdeterministic validationを実行する。
- canonical artifactを成果物単位でGit commit / pushする。
- 必要地点でWorkflow 90を呼び出し、control planeを実状態へ同期させる。
- Workflow 20へReview対象を引き渡す。
- Review返却後、対象版との対応が確認されたFindingのみをCoder修正へ適用する。
- 上流artifactを修正した場合、下流artifactへの影響を再評価する。

## 1.3. 担わない責務

- JSON field、required、enum、型、配列構造等のデータ構造定義。
- JSON Schema validation、ID重複、参照整合、taxonomy整合等の検査ロジック。
- commit graph比較ロジック。
- Notion control planeの直接取得・更新。
- Review Seq採番等のReview管理ロジック。
- Reviewの独立意味論判定。

# 2. インターフェイス

## 2.1. 入力

- `Entry_ID`

## 2.2. 主要出力

- `<Entry_ID>_00_sources.json`
- `<Entry_ID>_10_contents.json`
- `<Entry_ID>_20_analysis.json`

## 2.3. 副作用

- canonical artifactのGit commit / push。
- Workflow 90の呼出しによるcontrol plane同期。
- Workflow 20へのReview引渡し。

# 3. 依存する正本

## 3.1. 分析定義

- `docs/00_research_overview/10_urban_legend_analysis_axes_theoretical_design.md`
- `docs/00_research_overview/20_urban_legend_parent_child_code_system.md`
- `docs/00_research_overview/taxonomy_catalog.json` — code ID / Parent / Dimensionのmachine-readable構造正本
- `docs/00_research_overview/30_urban_legend_analysis_coding_rules.md`

## 3.2. 文書体系

- `docs/00_research_overview/90_ducumentation_metadata.md`

## 3.3. データ構造

- `schemas/00_sources.schema.json`
- `schemas/10_contents.schema.json`
- `schemas/20_analysis.schema.json`

## 3.4. 決定論的処理

- validation外部入口: `python -m src.validation.validate_entry <Entry_ID> [--through 00|10|20]`。省略時は `20` まで全検証。
- control plane同期: Workflow 90を介して `python -m src.status_management.sync_controlplane <Entry_ID>`
- `schema_validator.py` / `reference_validator.py` / `taxonomy_validator.py` およびstatus management内部モジュールは本Workflowから直接呼び出さない。

## 3.5. 関連Workflow

- `0000_workflow_20_review.md`
- `0000_workflow_90_sync_controlplane.md`

# 4. canonical artifactの依存関係

```text
<Entry_ID>_00_sources.json
        ↓
<Entry_ID>_10_contents.json
        ↓
<Entry_ID>_20_analysis.json
```

- `00_sources.json` は外部Evidenceの正本。
- `10_contents.json` はEvidenceから再構成した伝承内容の正本。
- `20_analysis.json` はContentに対する分析判断の正本。
- 下流artifactは上流artifactの本文を重複して正本化せず、必要な参照を保持する。
- 上流artifact変更時は下流artifactの妥当性を必ず再評価する。

# 5. 実行手順

## 5.1. Step 0: 対象確定と事前同期

1. `Entry_ID` に対応するEntryを解決する。
2. Entry境界を確認し、別EntryのEvidenceや分析を混入させない。
3. Workflow 90を実行する。
4. `BLOCKED / ERROR` の場合は作業を開始しない。
5. 既存コード、旧Excel、過去Reviewを独立判断前の正解として使用しない。

## 5.2. Step 1: 典拠調査とEvidence収集

- 一次資料・同時代資料を優先する。
- ミラー／転載／復刻、信頼できる二次資料・研究資料、後代のまとめ・解説を区別する。
- 一次資料が現存しない場合、その不在を隠さない。
- 「現在確認できる最古資料」と「実際の起源」を区別する。
- 後代資料にのみ現れる設定を、根拠なく初期形へ遡及しない。
- 資料に存在しない流通経路、条件、規則、心理、因果関係、結末、真相を推測で補完しない。
- 一次資料未発見、二次資料のみ、資料間競合、後代付加可能性、確認不能等の留保を保持する。
- Entry境界、Content再構成、後続分析に必要なEvidenceが揃った時点で探索を終了する。

## 5.3. Step 2: `00_sources.json` 作成

- Sourceと、そのSourceから実際に利用するEvidence unitを区別して記録する。
- 短い原文引用は必要最小限とし、参照位置を保持する。
- SourceのEvidence上の役割、一次資料との関係、不確実性を失わない。
- 作成後 `python -m src.validation.validate_entry <Entry_ID> --through 00` を実行する。
- validation failure時はGit確定へ進まない.
- validation通過後、`00_sources.json` だけを対象とするcommitを作成しpushする。
- commit後にWorkflow 90を実行する。

## 5.4. Step 3: `10_contents.json` 作成

- `00_sources.json` のEvidenceのみを根拠として伝承内容を再構成する.
- Evidence / Content層とAnalysis層を分離する。
- 先に `content_units` をEvidence-faithfulに作成し、その後にsummaryへ残すべきsalient unitを選定する。
- salient unitは `summary.coverage_refs` に列挙する。全Contentを機械的に列挙せず、次のいずれかに該当し、欠落すると伝承の具体的意味・展開・境界が変わるunitを選ぶ。
  - 発動・遭遇・主要作用・主要転換・終端に必要な出来事／行動／帰結。
  - transformation、identity change、人物・対象の最終状態。
  - terminal scene、終端警告、最後の行動や余韻など、結末の意味を決める要素。
  - motif echo（怪異と被作用者の形態・行動・言語等の反復／類似）が意味形成上重要な場合の対応要素。
  - 禁忌・回避・制御規則のうち、物語展開または帰結を変えるもの。
  - variant境界を決める増補・脱落・再構成上の差。
  - 原因・正体・結末等について、断定可否を左右する主要な不確実性。
- summaryは**意味保存圧縮**であり、紹介文でもAnalysis用の概念要約でもない。`coverage_refs` の各Content unitについて、具体的に「何が起きるか」「何がどう変わるか」「どう終わるか」をsummaryだけから再構成できる密度を保つ。
- 分析コードに都合のよい抽象語へ置換して具体的意味を消してはならない。例えば「人格異変」「危害」「変容」とだけ要約して、怪異との類似、身体・行動の具体的変化、最終場面、identityの喪失表現等を落とさない。
- 具体的描写を保持する際もEvidenceを超えて強い存在論・因果へ変換しない。「怪異そのものへ変身した」と確定できない場合は、「怪異と同様の動きをする状態になり、元の人物ではなくなったかのように描かれる」のように、**具体的描写＋認識論的留保**を同時に保持する。
- `summary.narrative` と `summary.structure` は相互補完してよいが、重要な終端・transformation・identity・motif echoをstructureだけへ追いやってnarrativeから消さない。
- 物語型では主要な進行、転換、終端、未解決部分を再構成可能にする。
- 命題型では対象、条件、中心命題、作用または予測、帰結、回避・制御・利用、Evidence境界を再構成可能にする。
- 主要形と異伝・派生を区別する。ただしVersion Scopeはこの段階で確定しない。
- 「語りが途絶える」「その後不明」を死亡・失踪等へ変換しない。
- 不明、資料間競合、後代解釈を導入しないと決定できない事項は無理に閉じない。
- 作成後、当該段階までを `validate_entry.py` で検証する。
- validation通過後、`10_contents.json` だけを対象とするcommitを作成しpushする。
- commit後にWorkflow 90を実行する。

## 5.5. Step 4: Version Scope確定

- `00_sources.json` と `10_contents.json` 成立後にVersion Scopeを確定する。
- 初期形、主要形、後代異伝、派生形の境界をEvidenceに基づいて判断する。
- Scope外variantを消去せず、Content上の存在とAnalysis対象範囲を区別する。
- Version ScopeはD01〜D21の全判定で一貫して適用する。

## 5.6. Step 5: `20_analysis.json` 作成

- `macro_category` と `entry_type` をEntry内容に基づくcanonical分類として明示する。Notion運用stateへ代替保存しない。
- Version Scope内のContentを対象としてD01〜D21を独立に判定する。
- 理論設計、Parent / Child code system、coding rulesを正とし、本Workflow内でコード定義を再定義しない。
- 各Dimensionはコード値だけで終わらせず、判定根拠と当該伝承における具体的な現れ方を記述する。
- 判定根拠を `10_contents.json` の具体的Contentへ追跡可能にする。
- `U / NA / C` ではcoding rulesに従い理由を明示する。
- Evidence不足を推測で補完しない。
- Scope外異伝や後代解釈を分析対象へ無断で混入させない。
- taxonomy gapを既存Childや `U` で隠さない。
- 既存分析値との差分照合は独立判定完了後に行う。
- 作成後、当該段階までを `validate_entry.py` で検証する。
- validation通過後、`20_analysis.json` だけを対象とするcommitを作成しpushする。
- commit後にWorkflow 90を実行する。

## 5.7. Step 6: Review引渡し

- 3 canonical artifactのdeterministic validationがすべて通過していることを確認する。
- Workflow 90を実行し、control planeとGit状態が同期していることを確認する。
- Workflow 20へ `Entry_ID` を引き渡す。
- Review対象版、Review Seq、Review結果保存形式はWorkflow 20およびdeterministic処理側を正とする。

## 5.8. Step 7: Review返却とCoder修正

- Review返却後、最初にWorkflow 90を実行する。
- stale Review、control plane更新漏れ、Review対象より新しいCoder成果物、divergenceが検出された場合は修正を開始しない。
- 適用可能なFindingについてcanonical artifactを修正する。
- Review結果そのものをCoderが遡及改変しない。
- `00_sources.json` を修正した場合、`10_contents.json` と `20_analysis.json` への影響を再評価する。
- `10_contents.json` を修正した場合、Version Scopeと `20_analysis.json` への影響を再評価する。
- `20_analysis.json` のみの修正で上流へ影響がない場合、上流artifactを不要に更新しない。
- 修正したcanonical artifactごとにvalidation、単独commit / push、Workflow 90同期を実行する。
- 必要な修正後、再度Workflow 20へ引き渡す。

## 5.9. Step 8: 完了処理

- Workflow 20上で必要なReviewが完了した後、Workflow 90を実行してcontrol planeを最終同期する。

# 6. Git運用上の不変条件

## 6.1. canonical artifact単位のcommit

- `00_sources.json`、`10_contents.json`、`20_analysis.json` は原則として別commitで確定する。
- 異なるcanonical artifactを同一の成果物確定commitへ混在させない。

## 6.2. version state

- `pre-SHA` / `post-SHA` / Review対象SHAの比較・祖先判定はWorkflow 90およびPythonへ委譲する。
- 同期処理が安全に作業可能と判定した版だけを対象に作業する。

# 7. 停止条件

以下のいずれかに該当する場合は推測で続行せず停止する。

- `Entry_ID` から対象Entryを一意に解決できない。
- Entry境界を確定できない。
- deterministic validationが失敗した。
- Git commit / pushが失敗した。
- Workflow 90がstale Review、checkpoint不整合、divergence等を検出した。
- Review対象版と現在版の対応を確認できない。
- 依存するSchema、coding rules、taxonomy等の正本間に解消不能な矛盾がある。

# 8. 責務境界の不変条件

- **LLM = 意味論上の作成・判断**。
- **JSON Schema = データ構造契約**。
- **Python = deterministic enforcement**。
- **Workflow 20 = 独立意味論Review**。
- **Workflow 90 = control plane同期オーケストレーション**。
