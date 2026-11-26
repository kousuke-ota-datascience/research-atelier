# 任意の意味論的正規化 — 事例評価のsemantic overlay

## 入力

- baseline JSON：{{CASE_ASSESSMENTS_JSON}}
- baselineの正確なファイルバイト列のSHA-256（スクリプトで算出済み）：{{BASELINE_SHA256}}
- 対象case ID・factor ID（明示した対象範囲）：{{TARGET_KEYS}}
- 出力テンプレート：`semantic_overlay.template.json`
- 出力schema：`semantic_overlay.schema.json`

## タスク

後続分析のために、指定されたReview済みの `assessment_text` のみを意味論的に正規化し、独立したsemantic overlayを生成せよ。baselineは変更不可であり、overlayは任意の非正本の解釈である。

外部Sourceの探索、新たな事実の追加、Evidenceの再解釈、判定の変更、欠損値の補完を行ってはならない。`applicability`、`epistemic_status`、`canonical_status`、事例の採択判定、参照関係、IDおよびその他のbaselineフィールドを変更してはならない。

## 処理手順

指定されたcase ID・factor IDの組ごとに、以下を実行せよ。

1. 固定ファクター定義、`assessment_text`、`canonical_status` を併せて確認する。
2. 明示された属性と留保を分離する。タスク、適用範囲、対象集団、時間基準、指標、評価シナリオの区別を保持する具体的なフィールド名を用いる。`value_text` は原文の文字列、`unit` は単位が原文に明示される場合にその文字列（それ以外は `null`）、`source_excerpt` は値と単位を含む原文の正確な抜粋とする。実測と推定、導入前と導入後、異なるサブタスクは別々の属性として記録する。計算、単位変換、分母の推測、未知の値のfalse・0への置換、比較結果からの新たな判定は行わない。
3. 限定条件を原文のまま `limitations` に保持する。曖昧または一部が未知の節は原文を保持し、安全に分離できない属性は抽出しない。混合判定では非該当と未知のサブタスクを統合しない。`confirmation_scope` に数値が存在しても未知の属性が確認されたとはみなさない。明示された部分的事実とその限定条件のみを抽出する。非該当の行では原則として `attributes` を空配列とする。
4. `semantic_overlay.schema.json` に適合するJSONのみを返す。与えられたIDとハッシュをそのまま使用する。各 `value_text`、`source_excerpt`、`limitations` の要素は対応する `assessment_text` の完全一致する部分文字列でなければならない。安全に正規化できる情報がない場合は `entries` を空配列としてよい。

## 受入条件

以下のコマンドで検証する。

```sh
python tools/case_assessments/build.py INV-ID --overlay path/to/semantic_overlay.json
```

スクリプトはID、baselineのハッシュ、対象キーの一意性、原文抜粋の一致、schema適合性を確認する。ただし、属性名や値の帰属の意味論的妥当性はこの検証では保証されない。後続利用の前に別途人間またはsemantic reviewで確認すること。

overlayをReview済みcanonical artifactsに統合してはならない。また、baselineを自動的に置き換えてはならない。
