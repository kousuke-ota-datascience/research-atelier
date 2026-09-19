# 0. ドキュメント情報

## 0.1. 位置付け

本書は、1つの `Entry_ID` に対して、

```text
00_sources
    ↓
10_contents
    ↓
20_analysis
    ↓
Review
    ↓
必要なら修正
    ↓
再Review
```

を完了条件まで反復する、**本番Entry E2E実行の最上位オーケストレーション正本**である。

Workflow 00自身は、Evidence収集、Content再構成、D01〜D21判定、Review意味論、control plane整合判定を再実装しない。

- canonical作成・修正: Workflow 10
- 独立意味論Review: Workflow 20
- control plane同期: Workflow 90

へ責務を委譲し、Workflow 00は**実行順序、反復、停止、完了判定**だけを統括する。

## 0.2. 設計原則

- Workflow 00は、Workflow 10と同様に**Markdown WorkflowをLLMへ与えて実行するオーケストレーション仕様**であり、Workflow 00専用のPythonランナーを前提としない。
- ユーザーが指定する業務入力は原則 `Entry_ID` のみ。
- 00 → 10 → 20 の依存方向を崩さない。
- Reviewは00 / 10 / 20を同一Review Seqの1 cycleとして扱う。
- Findingがある場合、必要なartifactから修正を開始し、その下流を再評価する。
- 上流artifactを変更したら下流artifactを無条件に信用しない。
- deterministic validationを通過していないartifactをReviewへ渡さない。
- current artifactと最新Review targetが一致していない状態を完了とみなさない。
- Workflow 00はNotionを直接更新しない。
- Workflow 00はReview JSONを直接書かない。
- Workflow 00はD01〜D21やFinding内容を独自に再判定しない。
- Legacy、旧Excel、過去の旧体系成果物を新規分析時の意味論的正解として使用しない。

# 1. 目的

指定された1 Entryについて、調査開始からcanonical artifact生成、Review、Finding修正、再Review、control plane収束までを1回の本番E2E実行として完遂する。

正常終了時には、次をすべて満たす。

1. current `00_sources.json / 10_contents.json / 20_analysis.json` が存在する。
2. current 3 artifactがdeterministic validationをPASSしている。
3. 最新Review cycleの00 / 10 / 20がすべて `Pass`。
4. 最新Review targetのcommit SHA / blob SHAがcurrent canonical artifactと一致する。
5. Workflow 90実行後、control planeがcurrent Git / Review事実と整合している。
6. 未処理Finding、stale Review、divergence、未Review current artifactが残っていない。

# 2. 責務

## 2.1. 担う責務

- Entry_IDを唯一の公開入力として本番E2Eを開始する。
- Workflow 90で事前状態を同期・検査する。
- 現在状態に応じてWorkflow 10 / 20の次実行を決める。
- 00 → 10 → 20のdependencyを保つ。
- Review Finding後の修正cycleを反復する。
- 上流変更時のdownstream invalidationを保証する。
- Review cycle数の安全上限を管理する。
- 最終完了条件を検査する。
- 本番E2E結果を `PASS / BLOCKED / ERROR` で返す。

## 2.2. 担わない責務

- Source探索・Evidence採否の意味論。
- Content unit、summary、variant、uncertaintyの作成判断。
- Version ScopeおよびD01〜D21の意味論判定。
- JSON Schema / reference / taxonomy validationロジック。
- Review Findingの意味論判断。
- Review Seq採番・Review JSON保存。
- Git ancestry / blob比較ロジック。
- Notion stateの直接更新。
- Legacyとの差分監査。

# 3. インターフェイス

## 3.1. 呼出し時の入力

ユーザーはチャット上で次の2点を指定する。

1. 本Workflow Markdown。
2. `Entry_ID`。

業務入力として追加で必要なのは原則 `Entry_ID` のみとする。

例:

```text
0000_workflow_00_entry_pipeline.md に従って Entry_ID 0179 を実行せよ
```

repository path、Review Seq、開始artifact、Notion page ID、pre/post SHA等を通常のユーザー入力として要求しない。

## 3.2. 実行入口

Workflow 00の実行入口は**チャット上のWorkflow指示**である。

- LLMは本書を最上位オーケストレーション正本として読み、指定Entry_IDに対してWorkflow 10 / 20 / 90を必要な順序で実行する。
- Workflow 00専用のPythonランナーや公開CLIは必須としない。
- 各Workflowが委譲しているdeterministic処理だけは、既存のPython公開入口をそのまま使用する。
- Workflow 10 / 20 / 90の内部処理をWorkflow 00用に複製しない。

## 3.3. 実行結果

チャット上の最終報告では少なくとも次を返す。

- `result = PASS / BLOCKED / ERROR`
- `Entry_ID`
- latest Review Seq（存在する場合）
- BLOCKED / ERROR時のreason codeまたは停止理由
- canonical / Review / control planeの最終整合状態

Workflow 90内部の `PASS / UPDATED` はWorkflow 00の最終 `PASS` と同義ではない。Workflow 00の完了不変条件をすべて満たした場合のみ `PASS` とする。

# 4. 依存Workflow

## 4.1. Workflow 10

`0000_workflow_10_each_lore_analysis.md`

責務:

- 調査
- `00_sources.json`
- `10_contents.json`
- Version Scope
- `20_analysis.json`
- validation
- canonical commit / push
- Findingに対するCoder修正

Workflow 00はこれらを再実装しない。

## 4.2. Workflow 20

`0000_workflow_20_review.md`

責務:

- Review target freeze
- Review 00
- Review 10
- Review 20
- Review Seq
- Finding
- Verdict
- append-only Review JSON

Workflow 00はReview判断を再実装しない。

## 4.3. Workflow 90

`0000_workflow_90_sync_controlplane.md`

責務:

- Git / Review / Notion事実の同期
- stale / divergence / malformed state検知
- control plane収束

Workflow 00はNotionを直接操作しない。

# 5. canonical dependency

```text
00_sources
    ↓
10_contents
    ↓
20_analysis
```

このdependencyを本番E2E全体のinvalidation規則として使用する。

| 変更されたartifact | 必ず再評価する範囲 |
|---|---|
| 00 | 00 → 10 → 20 |
| 10 | 10 → 20 |
| 20 | 20 |

- 「再評価」は必ずしも全artifactを書き換えることを意味しない。
- 上流変更後、下流が意味論的に不変と判断できる場合でも、validationとReview対象整合は再確認する。
- 上流変更後の古いReviewをcurrent artifactへのPassとして流用しない。

# 6. 実行状態の分類

Workflow 00開始時に、Workflow 90およびGit / Review事実からEntryを次のいずれかへ分類する。

## 6.1. NEW

- canonical artifactが未作成、または00から新規着手が必要。

処理:

```text
Workflow 10
00 → 10 → 20
↓
Workflow 20
```

## 6.2. PARTIAL

- 00のみ、または00 / 10まで存在する。
- deterministic validation可能な最深artifactから継続可能。

処理:

- earliest missing / invalid downstream artifactからWorkflow 10を継続する。
- 上流がvalidation FAILなら上流から修正する。

## 6.3. REVIEW_READY

- 00 / 10 / 20がcurrentでvalidation PASS。
- current 3 artifactに対するReview cycleがまだ存在しない。

処理:

```text
Workflow 20
```

## 6.4. CORRECTION_REQUIRED

- latest applicable ReviewにFindingが存在する。
- Review targetと修正開始対象の対応が安全に確認できる。

処理:

```text
Workflow 10 correction
↓
validation
↓
Workflow 20 re-review
```

## 6.5. STALE_CURRENT

- latest ReviewはPassだが、そのReview targetよりcurrent artifactが新しい。

処理:

- current artifactを未Reviewとして扱う。
- validation後、Workflow 20へ送る。
- 古いPassをcurrent版へ流用しない。

## 6.6. COMPLETE

- current 3 artifactがvalidation PASS。
- latest Review targetがcurrent 3 artifactとexact一致。
- 00 / 10 / 20のlatest verdictがすべてPass。
- Workflow 90が `PASS / UPDATED` で収束。

処理:

- 新しいReview cycleやartifact commitを作らず `PASS` を返す。

## 6.7. BLOCKED_STATE

例:

- diverged Git state
- malformed Review history
- incomplete Review cycle
- Review target ahead
- duplicate control-plane rows
- unknown Status
- Entry境界を一意に解決不能
- Schema / coding rules / taxonomy間の解消不能矛盾

処理:

- 自動修復せず `BLOCKED`。

# 7. 本番E2E実行手順

## 7.1. Phase 0: Entry開始

1. `Entry_ID` を受領する。
2. Workflow 90を実行する。
3. `BLOCKED / ERROR` なら停止する。
4. current canonical / Review / control planeの状態を分類する。
5. COMPLETEなら新しい副作用を発生させず終了する。

## 7.2. Phase 1: canonical生成・修正

必要な場合、Workflow 10を実行する。

新規Entry:

```text
00_sources
  ↓ validation
10_contents
  ↓ validation
20_analysis
  ↓ validation
```

修正Entry:

- applicable FindingをWorkflow 10へ渡す。
- Finding対象artifactだけを機械的に書き換えるのではなく、Workflow 10が意味論上必要な**最上流修正点**を判断する。
- 例えばReview 10 Findingでも、Evidence不足が原因なら00修正へ遡ることを許容する。
- Workflow 00自身はFinding内容から修正本文を決めない。

各canonical commit後、Workflow 90を実行する。

## 7.3. Phase 2: deterministic validation

Review前に必ず次を満たす。

```text
python -m src.validation.validate_entry <Entry_ID> --through 20
```

- FAIL時はReviewへ進まない。
- validation failureが意味論修正を要求する場合はWorkflow 10へ戻す。
- infrastructure / parser / schema loading等の実行不能は `ERROR` とする。

## 7.4. Phase 3: Review cycle

Workflow 20を実行する。

Review cycleは常に:

```text
Seq N
├─ Review 00
├─ Review 10
└─ Review 20
```

の完全な3点セットとする。

一部artifactだけを新しいReview Seqとして保存しない。

## 7.5. Phase 4: Review結果分岐

### 全artifact Pass

```text
00 Pass
10 Pass
20 Pass
    ↓
Phase 6 最終収束
```

### Findingあり

```text
Review Finding
    ↓
Workflow 90
    ↓
correction start
    ↓
Workflow 10
    ↓
validation
    ↓
Workflow 20
```

へ反復する。

Verdict severity自体から修正artifactを決めない。

## 7.6. Phase 5: correction start event

`要修正 -> 再作業中` には明示的なCoder開始イベントが必要である。

ユーザーが本Workflowと `Entry_ID` を指定して**本番E2E全体の実行を依頼した事実**を、そのEntryに対する処理継続の明示意思とする。

その実行中にWorkflow 00が `CORRECTION_REQUIRED` を確認し、実際にWorkflow 10のcorrection phaseへ遷移した時点をcorrection start eventとする。

- 追加の公開CLIや追加ユーザー引数を要求しない。
- Entry_IDが存在するだけで「修正開始」と推測しない。
- **明示されたWorkflow 00実行要求 + CORRECTION_REQUIRED確認 + correction phaseへの実遷移**の組合せを開始イベントとする。
- correction start eventはWorkflow 90へ内部イベントとして渡す。
- Workflow 90はcurrent `reconcile.py` のdeterministic ruleで適用可否を検査する。
- current artifact / control plane post-SHA / latest non-Pass Review targetがexact一致しない場合はBLOCKする。
- 同じeventの重複実行はidempotentとする。

これにより `要修正 -> 再作業中` はEntry_IDからの推測ではなく、Workflow 00の実遷移イベントとして決定論化する。

## 7.7. Phase 6: 最終収束

最後にWorkflow 90を実行する。

以下をすべて確認する。

```text
current 00
  = latest Review 00 target

current 10
  = latest Review 10 target

current 20
  = latest Review 20 target

latest Review 00 = Pass
latest Review 10 = Pass
latest Review 20 = Pass

validate_entry --through 20 = PASS

Workflow 90 = PASS or UPDATED
```

すべて成立した場合のみWorkflow 00は `PASS` を返す。

# 8. Review Finding後のinvalidation

## 8.1. Review 00 Finding

原則:

```text
00修正
↓
10再評価
↓
20再評価
↓
新Review cycle
```

## 8.2. Review 10 Finding

原則:

```text
10修正
↓
20再評価
↓
新Review cycle
```

ただし、Finding原因がSource / Evidence不足である場合、Workflow 10は00まで遡ってよい。

## 8.3. Review 20 Finding

原則:

```text
20修正
↓
新Review cycle
```

ただし、Finding原因がVersion Scope、Content再構成、Evidence不足にある場合、Workflow 10は10または00まで遡ってよい。

## 8.4. 不変条件

- Workflow 00は「Review 10だから10だけ直す」のような固定的artifact mappingを行わない。
- **最上流の意味論的不具合箇所はWorkflow 10が判断する。**
- Workflow 00はその結果に応じてdownstream invalidationを適用する。

# 9. 反復上限

Review → correction → re-reviewが無限に継続しないよう、1回のWorkflow 00実行にはcycle上限を設ける。

初期運用値:

```text
MAX_REVIEW_CYCLES_PER_RUN = 5
```

- 通常のユーザー入力にはしない。
- 同一Entryについて1回のpipeline実行中に新規Review cycleを5回作成してもPassへ収束しない場合、`BLOCKED` とする。
- qualityを5回で打ち切るという意味ではない。
- 自動オーケストレーションを停止し、人間による設計・Evidence・taxonomy・Finding反復原因の確認へ上げる安全装置である。

推奨reason code:

```text
MAX_REVIEW_CYCLES
```

# 10. Idempotency

Workflow 00はEntry単位でidempotentに近い挙動を持つこと。

COMPLETE Entryに対して再実行した場合:

1. Workflow 90で状態確認。
2. current artifactsとlatest Review targetのexact一致を確認。
3. validation PASSを確認。
4. latest 00 / 10 / 20がPassであることを確認。
5. 新しいartifact commit / Review cycleを作らず `PASS`。

「実行したから新しいReview Seqを作る」という挙動は禁止する。

# 11. semantic leakage防止

## 11.1. 新規生成時

次を意味論的正解として使用しない。

- Legacy artifact
- 旧Excel
- 過去の旧体系Review
- 過去の旧taxonomy code
- E2E regressionで固定された旧Content ID

外部Evidenceと現行Workflow / Schema / taxonomy / coding rulesを正とする。

## 11.2. correction時

current canonical artifactと、そのcurrent版に対するapplicable Review Findingは修正入力として使用してよい。

ただし、

- 過去Review cycleの結論を新しいEvidenceより優先しない。
- 旧Content IDや旧codeを「一致すべき期待値」としない。
- Review Findingを直すためにEvidenceにない意味を付加しない。

# 12. Git運用

- canonical artifactのcommit単位はWorkflow 10に従う。
- Review cycle commitはWorkflow 20に従う。
- Workflow 00はartifact本文・Review JSONを直接commitしない。
- current artifact SHAとReview target SHAの関係はWorkflow 90 / Pythonへ委譲する。
- Review結果ファイル自身のcommit SHAをcanonical artifact SHAとして扱わない。

# 13. control planeとの関係

Workflow 00からNotionを直接更新しない。

呼出し点:

```text
開始前
canonical commit後
Review write後
correction開始時
correction commit後
最終完了時
```

で必要に応じWorkflow 90を実行する。

Workflow 90の `PASS / UPDATED` は後続処理可能。

`BLOCKED / ERROR` はWorkflow 00を停止させる。

# 14. 停止条件

以下では推測で継続しない。

- Entry_IDを一意に解決できない。
- Workflow 90がBLOCKED / ERROR。
- deterministic validation FAILを解消できない。
- Git commit / push失敗。
- Review history malformed / incomplete。
- current artifactとReview targetがdiverged。
- Findingの根因を安全に修正できない。
- Evidence不足のまま意味論を補完しないと先へ進めない。
- Schema / taxonomy / coding rules間に解消不能な矛盾がある。
- MAX_REVIEW_CYCLES_PER_RUNへ到達。

# 15. 本番E2EとE2E Test Protocolの関係

本番とテストで、00 → 10 → 20 → Review loopの意味論を二重実装しない。

```text
                    共通処理
                       │
             Workflow 00 Entry Pipeline
                       │
          00 → 10 → 20 → Review loop
                 ┌─────┴─────┐
                 │           │
              Production   E2E Test
                 │           │
              main        isolated branch /
              canonical   candidate workspace
                 │           │
              Notion      production stateを
              sync        汚染しない
```

`0000_e2e_test_protocol.md` はWorkflow 00と同じ処理規則を隔離環境で実行し、

- 既存canonical
- Legacy
- 過去Review

をblind generation / blind Review中の期待値として見ない。

candidate freeze後にだけ差分監査を行う。

# 16. 実行モデル

Workflow 00はMarkdownによるLLMオーケストレーションとして実行する。

```text
User
  └─ Workflow 00 Markdown + Entry_ID
                    ↓
                  LLM
                    ↓
       current state / Workflow 90確認
                    ↓
             Workflow 10実行
                    ↓
          deterministic validation
                    ↓
             Workflow 20実行
                    ↓
              verdict確認
                    ↓
          correction / finalize
```

## 16.1. Workflow 00専用Pythonを前提にしない

現行運用ではWorkflow 10自体がPythonランナーからkickされておらず、MarkdownとEntry_IDをLLMへ与えて実行している。Workflow 00も同じ実行モデルに統一する。

将来、完全自動実行基盤が必要になった場合に別途実装してよいが、それをWorkflow 00の意味論・公開インターフェイス・必須実行条件にはしない。

## 16.2. Pythonを使用する範囲

PythonはLLMオーケストレーションの代替ではなく、deterministic enforcementに限定する。

代表例:

```text
python -m src.validation.validate_entry <Entry_ID> [--through 00|10|20]
python -m src.reviewing.review_writer prepare <Entry_ID>
python -m src.reviewing.review_writer write <Entry_ID>
```

- Workflow 00は上記の内部ロジックを再実装しない。
- Workflow 10 / 20 / 90が定める責務境界をそのまま利用する。
- Workflow 90の本番I/OはGitHub / Notion connectorを使い、state transitionはcurrent `reconcile.py` をdeterministicに実行する。
- 意味論上の「次に何をするか」はWorkflow 00を読んだLLMが判断し、機械的に一意なvalidation / Review保存 / control-plane収束は各deterministic実装へ委譲する。

# 17. 完了不変条件

Workflow 00の `PASS` は、次の論理積を意味する。

```text
VALID(current 00 / 10 / 20)
AND
LATEST_REVIEW_TARGET == current 00 / 10 / 20
AND
LATEST_REVIEW_VERDICT(00) == Pass
AND
LATEST_REVIEW_VERDICT(10) == Pass
AND
LATEST_REVIEW_VERDICT(20) == Pass
AND
CONTROL_PLANE_SYNCHRONIZED
AND
NO_UNRESOLVED_FINDING
AND
NO_STALE_OR_DIVERGED_STATE
```

この条件を満たさないEntryを、部分的な成功のみを理由に `PASS` としてはならない。

# 18. 責務境界の最終形

```text
Workflow 00
  = production E2E orchestration / iteration / completion

Workflow 10
  = research / canonical generation / correction

Workflow 20
  = independent semantic Review

Workflow 90
  = control-plane synchronization

JSON Schema
  = data structure contract

Python validation
  = deterministic enforcement

Git JSON
  = canonical artifact / Review fact

Notion
  = operational current state
```
