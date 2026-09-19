# 1. Research overview ドキュメント一覧と責務分担

`docs/00_research_overview/` 配下の各文書は、同じ分析体系を異なる抽象度・目的で記述する。内容の重複による不整合を避けるため、各文書の責務を以下のとおり分離する。

## 1.1. ドキュメント別の責務・記載内容

- `10_urban_legend_analysis_axes_theoretical_design.md`
    - 責務:
        - 理論設計
    - 主に記載する内容:
        - なぜその概念次元を置くのか
        - 各次元が何を測るのか
        - 次元間の理論的境界
        - 分析単位
        - データ型
        - 情報量評価の原則
        - 研究問いとの対応
    - 原則として記載しない内容:
        - Parent / Childコードの完全一覧
        - 個別コードのinclude / exclude条件
        - 具体的な判定フロー

- `20_urban_legend_parent_child_code_system.md`
    - 責務:
        - 測定体系・コード体系
    - 主に記載する内容:
        - 各理論次元をどのParent / Child / Value / bitで測定するか
        - コードID
        - Child → Parent対応
        - 各カテゴリの定義
        - 各次元の測定粒度
        - Parent / Child、Primary / Secondaryの実装上の関係
    - 原則として記載しない内容:
        - 新しい理論次元の独自導入
        - 理論次元そのものの意味変更
        - 証拠からコードへ到達する詳細な操作手順

- `taxonomy_catalog.json`
    - 責務:
        - D01〜D21 taxonomyのmachine-readable構造正本
    - 主に記載する内容:
        - catalog version
        - Dimension IDと型
        - code_id
        - Child → Parent対応
        - code_idが属するDimension
    - 原則として記載しない内容:
        - コードの意味論的定義・解説
        - Evidenceからコードへ到達する判定規則
    - 運用:
        - Python validatorは本JSONのみをtaxonomy構造検査に使用する
        - `20_urban_legend_parent_child_code_system.md` はラベル・定義・意味論の正本として維持し、実行時にMarkdownをparseしない

- `30_urban_legend_analysis_coding_rules.md`
    - 責務:
        - 分析コード付与運用規則
    - 主に記載する内容:
        - 実際の資料・証拠からどのようにコードを判定するか
        - Evidence role
        - Dimension Status
        - Primary / Secondary選択規則
        - include / exclude条件
        - 境界事例
        - 判定フロー
        - 不明・競合・非該当の扱い
    - 原則として記載しない内容:
        - 理論次元そのものの新設・廃止
        - Parent / Child / Value / bit体系の独自変更

- `80_appendix/`
    - 責務:
        - 現行Research Overviewを理解するための正式な補足資料群
        - 理論設計の変更履歴
        - 初見読者向けの概念解説
        - 現行仕様から分離して保存すべき凍結済み歴史資料
    - 主に記載する内容:
        - `10_analysis_axes_theory_history/`: 現行分析体系に至る設計変更履歴と過去版
        - `20_what_is_sense_making.md`: sense-making / 意味形成の補足説明、本研究での操作的位置付け
    - 原則として記載しない内容:
        - 現行理論・測定体系・分析コード付与規則の独自な再定義
        - `10` / `20` / `30`と競合する現行仕様

- `90_ducumentation_metadata.md`
    - 責務:
        - 文書管理規則
    - 主に記載する内容:
        - Research overview文書群の責務分担
        - 文書構造
        - 見出し番号
        - ディレクトリ・ファイル命名規則
        - 記載上の共通ルール
        - Appendixの位置付けと正本関係
        - 個別伝承tutorialの位置付けと正本関係
    - 原則として記載しない内容:
        - 個別の理論内容
        - 個別のコード値・カテゴリ定義
        - 個別伝承の分析コード付与判定

## 1.2. 責務分担の基本原則

### 1.2.1. 抽象化階層

Research overview文書群は、以下の順に理論から運用・補足へ具体化する。

- `10` は **「なぜ・何を測るか」** を定義する。
- `20` は **「それをどの値で測るか」** を定義する。
- `30` は **「証拠からその値をどう判定するか」** を定義する。
- `80` は **「なぜ現在の設計になったか／中核概念をどう理解するか」** を補足する。
- `90` は **「これらの文書をどう管理・構造化するか」** を定義する。

`20` は `10` の理論を測定可能なコードへ具体化し、`30` は `20` のコードを再現可能に適用するための判定規則へ具体化する。`80` は現行仕様を再定義せず、設計履歴・概念理解・凍結版保存を担う。

### 1.2.2. 重複記載と参照

- 同一内容を複数文書へ完全複製しない。
- 別文書の詳細が必要な場合は、その文書の責務範囲を侵食しない要約に留め、正本となる文書を参照する。
- 理論上の理由は `10`、コード体系の完全定義は `20`、具体的判定手順は `30` に集約する。
- 理論設計の変更理由・廃止案・過去仕様は `80_appendix/10_analysis_axes_theory_history/` に集約する。
- sense-makingの初見読者向け解説は `80_appendix/20_what_is_sense_making.md` に集約する。
- 他文書に同一情報を再掲する場合は、当該文書の理解に必要な最小限の情報に限定する。

### 1.2.3. 変更起点と波及確認

- 理論次元の追加・削除・意味変更は `10` を起点として行う。
    - 変更後、必要に応じて `20` の測定体系と `30` の判定規則を更新する。
    - 変更理由・旧設計との差分を研究履歴として残す必要がある場合は、`80_appendix/10_analysis_axes_theory_history/README.md` も更新する。
- Parent / Child / Value / bitの追加・削除・統合・分割は `20` を起点として行う。
    - 変更後、`10` の理論定義との整合性と、`30` の判定規則への影響を確認する。
- 証拠要件・判定フロー・Primary / Secondary選択規則などの運用変更は `30` を起点として行う。
    - 変更後、必要に応じて `20` のコード定義および `10` の理論定義との整合性を確認する。
- Appendixの説明追加・整理は `80` 内で行う。
    - Appendixは説明のために `10` / `20` / `30` の現行仕様を独自に変更してはならない。
- 文書構造・見出し・命名規則などの管理規則変更は `90` を起点として行う。
    - 変更後、対象文書群に対して構造上の整合性を確認する。
- 個別伝承分析の標準作業手順、control plane interface、Coder側Review修正cycleの変更は `docs/10_each_lore/0000_tutorial/0000_workflow_10_each_lore_analysis.md` を起点として行う。
    - 変更後、`0000_00_contents.md`、`0000_10_analysis.md`、`0000_workflow_20_review.md`、`10` / `20` / `30` / `90` と競合しないことを確認する。
- 個別伝承Reviewの標準作業手順変更は `docs/10_each_lore/0000_tutorial/0000_workflow_20_review.md` を起点として行う。
    - Coder側の状態遷移・pre/post-SHA更新規則をReview workflow側で独自に再定義しない。

### 1.2.4. 文書間で競合した場合の正本

文書間で記載が競合した場合、以下を当該責務範囲の正本とする。

- 現行の理論概念・概念次元・次元間境界: `10_urban_legend_analysis_axes_theoretical_design.md`
- Parent / Child / Value / bit・コードID・カテゴリ定義: `20_urban_legend_parent_child_code_system.md`
- 証拠要件・具体的判定・分析コード付与手順: `30_urban_legend_analysis_coding_rules.md`
- 理論設計の変更履歴・変更理由・過去版との対応関係: `80_appendix/10_analysis_axes_theory_history/README.md`
- 文書構造・見出し番号・命名規則・文書管理: `90_ducumentation_metadata.md`
- 個別伝承分析・control plane interface・Coder側Review修正cycle: `docs/10_each_lore/0000_tutorial/0000_workflow_10_each_lore_analysis.md`
- 個別伝承Review手順・Review Seq・Review結果フォーマット: `docs/10_each_lore/0000_tutorial/0000_workflow_20_review.md`
- 個別伝承 `00_contents` の記載様式: `docs/10_each_lore/0000_tutorial/0000_00_contents.md`
- 個別伝承 `10_analysis` の記載様式: `docs/10_each_lore/0000_tutorial/0000_10_analysis.md`

`80_appendix/10_analysis_axes_theory_history/` 内の過去版ファイルは、**当時の仕様を保存した凍結済み歴史資料**であり、現行仕様の正本ではない。

`80_appendix/20_what_is_sense_making.md` は概念理解のための補助文書であり、現行の理論定義と競合する場合は `10_urban_legend_analysis_axes_theoretical_design.md` を優先する。

競合を発見した場合、当該責務の正本側に合わせて他文書を修正し、不一致を残さない。

# 2. 文書構造ルール

- 見出しには必ず、対応するレベルの接頭辞番号を付けること。
- 接頭辞番号は上位見出しの番号を継承すること。
- 同一階層の見出しは連番とすること。
- 見出しレベルを飛ばさないこと。
- 見出しレベル1を単独のドキュメントタイトルとして使用してはならない。
- 同一見出し階層内において、その数が一つの見出しを作成してはならない（*1）。
- 原則として、以下で指定された章・節を省略しないこと。
- 見出しを追加する場合も番号体系を維持すること。

| 見出しレベル | 接頭辞番号 | 見出し名称（日本語） | 見出し名称（英語） |
|---|---|---|---|
| # | 1. | 章 | chapter |
| ## | 1.1. | 節 | section |
| ### | 1.1.1. | 項 | subsection |
| #### | 1.1.1.1. | 目 | subsubsection |

*1）例

```text
# 1. aaa
## 1.1. aaa-1
### 1.1.1. aaa-1-1
### 1.1.2. aaa-1-2
```

この場合、`## 1.1. aaa-1` は、その見出しレベル（≒カテゴリ）に子見出しが1つしか存在しないため、独立した階層を作成する意味がない。

# 3. 伝承別ディレクトリ・ファイル命名規則

## 3.1. Entry_ID と接頭辞番号

`docs/10_each_lore/` 配下に作成する各伝承エントリのディレクトリは、以下の形式とする。

```text
<4桁ゼロ埋めEntry_ID>_<伝承識別名>
```

接頭辞番号には、`docs/20_analysis_summary/urban_legend_parent_child_full_application_v1.xlsx` に記載された当該伝承の `Entry_ID` を使用し、**4桁のゼロ埋め**で表記する。

例:

```text
Entry_ID = 180
→ 0180_kisaragi_station
```

ディレクトリの並び順、作成順、調査順を根拠として独自に番号を採番してはならない。伝承エントリとディレクトリの対応は、上記Excelの `Entry_ID` を正本とする。

新規調査・再調査・既存伝承の文書化を行う際は、作業開始前に対象伝承の `Entry_ID` を確認し、その4桁ゼロ埋め値をディレクトリ接頭辞として使用する。

## 3.2. 個別伝承ファイルの命名規則

各伝承ディレクトリ内の主要ファイルにも、ディレクトリと同じ4桁ゼロ埋め `Entry_ID` を接頭辞として付与する。

```text
<4桁ゼロ埋めEntry_ID>_00_contents.md
<4桁ゼロ埋めEntry_ID>_10_analysis.md
```

例:

```text
0180_kisaragi_station/
├── 0180_00_contents.md
└── 0180_10_analysis.md
```

ファイル単体で移動・抽出・参照された場合にも伝承エントリを一意に識別できるよう、`00_contents.md`、`10_analysis.md` のような接頭辞なしファイル名は使用しない。

## 3.3. 予約番号とtutorial

`0000` はテンプレート・チュートリアル用の予約番号とし、実データの伝承エントリには使用しない。

```text
docs/10_each_lore/0000_tutorial/
├── 0000_00_contents.md
├── 0000_10_analysis.md
├── 0000_workflow_10_each_lore_analysis.md
├── 0000_workflow_20_review.md
├── 0000_workflow.md        # legacy redirect
└── 0000_review.md          # legacy redirect
```

各ファイルの責務は以下とする。

- `0000_workflow_10_each_lore_analysis.md`
    - 個別伝承エントリ1件について、**伝承内容 / Evidence整理 → 分析コード付与**を実行する標準作業手順の正本。
    - Coder側のcommit / push、control plane interface、Status / pre-SHA / post-SHA更新、Review返却後の修正cycleを定義する。
    - control planeの実体パスをハードコードせず、実行時に外部指定されたcontrol planeへ規定フォーマットで読み書きする。
- `0000_workflow_20_review.md`
    - 個別伝承00/10のReview標準作業手順の正本。
    - Review対象commit / blobの固定、Review Seq、Findings、Pass / 要修正判定、Review mdフォーマットを定義する。
    - Coder成果物の修正やcontrol planeの状態遷移を独自に実行しない。
- `0000_00_contents.md`
    - 伝承内容 / Evidence整理の記載様式・章構造・要求密度の正本。
- `0000_10_analysis.md`
    - 分析コード付与結果の記載様式・章構造・要求密度の正本。
- `0000_workflow.md` / `0000_review.md`
    - 過去文書からの参照互換性のためだけに保持するlegacy redirect。現行正本として使用しない。

実データの伝承ディレクトリでは、接頭辞番号とExcel上の `Entry_ID` が一致していることを確認する。ディレクトリ名の伝承識別名部分を変更しても、同一Entryである限り接頭辞番号は変更しない。

`docs/99_work/` 配下のhandoff・control plane・作業メモは、作業途中状態やフェーズ固有の状態を記録する領域である。control planeは現在状態のインスタンスを保持し、恒久的な作業手順・状態遷移規則・SHA整合性判定を独自に正本化しない。

# 4. Appendix 管理規則

## 4.1. `80_appendix/` の位置付け

`80_appendix/` は `docs/00_research_overview/` の正式な構成要素であり、`docs/99_work/` のような一時的作業領域ではない。

ただしAppendixは、現行仕様を定義する `10` / `20` / `30` と同じ責務を持たない。主目的は、**設計履歴、概念理解、凍結済み歴史資料を、現行仕様から分離しながら正式に保存すること**である。

## 4.2. `10_analysis_axes_theory_history/`

`80_appendix/10_analysis_axes_theory_history/README.md` を、分析理論軸の**変更履歴・設計判断・版対応関係の正本**とする。

同ディレクトリに保存する `urban_legend_analysis_axes_theoretical_design_v*.md` は、各時点の設計を保持する凍結済み歴史資料とする。

過去版は改変して現行仕様へ合わせない。誤記訂正等が必要な場合も、歴史資料としての同一性を壊さない方法を優先する。

現在有効な理論仕様の確認には、必ず `../../10_urban_legend_analysis_axes_theoretical_design.md` を使用する。

## 4.3. `20_what_is_sense_making.md`

`80_appendix/20_what_is_sense_making.md` は、初見読者が本研究の中核概念である `sense-making / 意味形成` を理解するための補助文書とする。

特に、以下の区別を明示する。

- sense-makingという形成・交渉・流通の**過程**
- 伝承エントリに表現されたsense-makingの**モデル／産物／痕跡**

本研究の21概念次元が直接コードする主対象は後者であり、形成・流通過程そのものを心理的・歴史的因果として断定するには別種の証拠が必要であることを明記する。

本文書は理論理解を補助するが、現行21概念次元を独自に新設・削除・再定義してはならない。
