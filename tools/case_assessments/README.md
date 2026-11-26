# 事例評価の派生成果物生成ツール（事例比較固有契約 v1）

本ツールは、INV-000046で採用した事例・ファクター比較の固定契約に従い、Review済みの調査結果を再利用可能なJSONへ変換するための任意の補助ツールである。

**新たなcanonical artifactやWorkflow 00 / 10 / 20の完了条件を定義するものではない。** 異なる調査形式には、それぞれの契約またはadapterが必要となる。

## 格納先と責務

- `tools/case_assessments/`：生成スクリプト、局所的なJSON Schema、テンプレート、意味論的正規化用プロンプト、単体テストを一体として管理する。Research workflowの正本実装や正本schemaとは分離する。
- `investigations/<INV-ID>/derived/case_assessments.json`：各Investigationから生成した派生成果物を格納する。ツール自体はInvestigation固有のディレクトリに複製しない。

現行architectureの `docs/00_management/0001_research_architecture.md` および `0003_canonical_artifact_chain.md` のsingle-authority ruleに従う。なお、`docs/98_reusable_artifact/` は旧workflow由来の参照資料であり、本ツールの格納先ではない。本ディレクトリの配置はこの補助ツールについての判断であり、リポジトリ全体の新しい正本仕様を追加するものではない。

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `build.py` | 決定論的な抽出、Review・Finalizationの確認、K → E → Sourceのlineage展開、完全性・schema検証、再生成一致検証 |
| `case_assessments.schema.json` | 派生成果物固有のJSON Schema。正本の `schemas/v2/` とは独立 |
| `case_assessments.template.json` | 出力構造を示すテンプレート。placeholderを含むため、そのままではschemaに適合しない |
| `semantic_normalization.prompt.md` | 任意の意味論的正規化を行うための再利用可能なLLMプロンプト |
| `semantic_overlay.template.json` | 意味論的正規化結果の出力テンプレート |
| `semantic_overlay.schema.json` | 正規化結果（semantic overlay）固有のJSON Schema |
| `test_build.py` | 抽出処理および異常入力拒否の単体テスト |

## 実行方法

Git checkout上でPython 3.10以上と `jsonschema` を使用する。リポジトリのルートから以下を実行する。

```sh
python tools/case_assessments/build.py INV-000046
python tools/case_assessments/build.py INV-000046 --check
```

第1コマンドは生成、第2コマンドは保存済みJSONと再生成結果の完全一致を検証する。

前提条件は、現行のcommit済みcanonical chainに対する最新のReviewがPASSであること、および同じAnalysis blobについて正本のprojection logがSUCCESSであること。既存のthrough-30 validatorとReview history helperを利用し、正本の判定規則は再実装しない。

frozen Contextから参照frameworkのRQ / INV / commit / blobを取得し、固定ファクター定義と各事例の採択条件・判定を抽出する。入力形式の変化、ファクターの欠損・重複・順序不整合、参照不整合、Review対象の不一致、Finalizationの未完了を検出した場合は処理を停止する。生成器で入力を暗黙に修正して成功させてはならない。

出力先は `investigations/<INV-ID>/derived/case_assessments.json` である。生成時刻に依存する値は追加せず、同じcommit済み入力から同一バイト列を生成する。事例数は入力から取得し、固定値としない。R1～R4の4条件は本事例比較固有の契約であり、異なる採択条件を用いる場合はadapterまたは契約versionを明示して対応する。

`factor_framework` には参照元のファクター定義を原文のまま保存する。定義文に含まれるK参照はframework側のInvestigationに属し、事例側のK参照とは別の名前空間である。

## フィールドの意味と保持規則

- `canonical_line` と `analysis_line` は、Review済み `working_answer.text` の原文行と1始まりの行番号を表す。JSONファイル自体の行番号ではない。
- `assessment_text` は部分的に確認できた事実、未知の情報、限定条件、留保を含む判定文全体を保持する。`value` は該当する行でのみこの文を格納し、それ以外は `null` とする。原文は削除しない。`limitations: null` は限定条件を別フィールドへ抽出していないことを意味し、限定条件が存在しないことを意味しない。
- `canonical_status` はAnalysisに記録された原文の判定ラベルである。「未知」を `undetermined` に対応付けても、適用可否自体が未知なのか属性値のみが未知なのかは推測しない。混合判定ではサブタスクごとの原文を保持する。`reported` は行全体の原文ラベルに由来する区分であり、各節がすべて確立済みの事実であることを保証しない。
- `reference_role: confirmation_scope` は未知・未確認の判定に用いた確認範囲を示す。K / E / Sourceへの参照は推移的なlineageであり、未知の属性に対する肯定的証拠を意味しない。`basis` も原文の根拠範囲を保持する。事例見出しの `source_refs` と各判定行の参照は区別する。
- 生成時に数値推定、再分類、新規Evidenceの取得、意味論的な再判断は行わない。

## 任意の意味論的正規化

後続分析で属性値の分解が必要な場合のみ、プロンプトとoverlayテンプレートを使用する。入力としてbaseline JSON、正確なファイルバイト列のSHA-256（例えば `sha256sum` で取得）、対象のcase ID・factor IDを渡す。結果はbaselineとは別の非正本artifactとして保持する。

```sh
python tools/case_assessments/build.py INV-000046 --overlay path/to/semantic_overlay.json
```

この検証ではbaselineの再生成一致、schema、参照先、原文抜粋との一致を確認する。フィールド名や属性への帰属の意味論的妥当性は機械検証だけでは保証できないため、利用前に別途人間またはsemantic reviewによる確認が必要である。overlayをbaselineへ自動統合・承認してはならない。今回の原文保持型baselineの生成にはoverlayを必要としない。

将来Working Answerの形式が本契約から外れた場合は、処理を停止し、テスト済みの決定論的adapterを追加するか、承認済みAnalysisから原文参照を保持した意味論的抽出を別途レビューする。LLMプロンプトでparserの失敗を暗黙に回避したり、正本を変更したりしてはならない。

CSVはJSONからの派生projection（1事例×1ファクターを1行とする形式）であり、独立した正本ではない。
