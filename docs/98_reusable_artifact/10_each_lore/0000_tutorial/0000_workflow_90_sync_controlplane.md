# 0. ドキュメント情報

## 0.1. 位置付け

本書はcontrol plane同期・整合確認を一元管理するオーケストレーションの正本である。

## 0.2. 設計原則

- ユーザーからの業務入力は `Entry_ID` のみ。
- control planeのcurrent state保持先はNotion `伝承エントリ調査状況`。
- Git上のcanonical artifactとReview結果JSONを事実源としてNotion stateを収束させる。
- **本番チャット経路のI/OはGitHub / Notion connectorを使用する。**
- **Status収束・fail-stop・mutation planの唯一の決定論的正本は `src/status_management/reconcile.py` とする。**
- connector経路でも `reconcile.py::reconcile_payload()` を実行し、LLMが同じstate transition rulesを文章から再実装しない。
- `sync_controlplane.py` はNotion Public API tokenを持つ外部batch環境向けoptional adapterとし、本番チャット経路の必須入口にはしない。
- Workflow 90自身は研究内容、Review意味論、D01〜D21を判定しない。

# 1. 目的

指定Entryについて、Notion control planeの状態とGit上のcanonical artifact・Review結果JSONの状態を比較し、同期可能な範囲でcurrent stateを正しい状態へ収束させる。

# 2. インターフェイス

## 2.1. 入力

公開入力:

- `Entry_ID`

内部イベント:

- `correction_started: [Artifact...]`
  - Workflow 00が実際にcorrection phaseへ遷移した時だけ発行する。
  - ユーザー入力にはしない。
  - `Entry_ID` やReview存在だけから推測しない。
  - `reconcile.py` が適用可能性を決定論的に検査する。

## 2.2. 出力

- canonical artifactは生成しない。
- 同期結果を `PASS / UPDATED / BLOCKED / ERROR` のいずれかとして返す。
- 詳細は必要時のみreason / rule ID / remarks / 実行ログへ残す。
- `PASS / UPDATED / BLOCKED / ERROR` はWorkflow 90の実行結果であり、control planeの `Status` 値ではない。

# 3. 管理単位

- 論理単位は `(Entry_ID, 成果物)`。
- `成果物` は `00 / 10 / 20`。
- Notionの `key` はtitle制約用であり、意味論的主キーにしない。

# 4. 対象state

- `Entry_ID`
- `伝承`
- `成果物`
- `Status`
- `最新レビュー版`
- `pre-SHA`
- `post-SHA`
- `remarks`

## 4.1. Status正本

`Status` は以下の7値のみを許容する。

| Status | 定義 |
|---|---|
| `未` | Coder作業未着手 |
| `レビュー待` | 初回Coder成果物commit完了、初回Review待ち |
| `要修正` | Reviewで修正要求が確定し、修正成果物commit前 |
| `再作業中` | CoderがReview指摘への修正作業中 |
| `再レビュー待` | 修正成果物commit完了、再Review待ち |
| `完了` | 対象artifactの最新ReviewがPass |
| `－（対象外）` | 当該成果物を適用対象外と明示した状態 |

- Notion `伝承エントリ調査状況.Status` のSelect optionsを機械的許容値の正本とする。
- `reconcile.py` は上記7値以外を受け入れずBLOCKする。
- `－（対象外）` はGit / Review事実だけから自動付与しない。

## 4.2. Status遷移

Legacy標準Workflowで確定していた状態遷移を継承する。

| イベント | Status | 最新レビュー版 | pre-SHA | post-SHA |
|---|---|---|---|---|
| 初回Coder成果物commit完了 | `レビュー待` | 変更なし | 編集入力checkpoint | 新成果物commit |
| Reviewで修正要求確定 | `要修正` | 実施済みReview Seq | 変更なし | 変更なし |
| Review Pass確定 | `完了` | 実施済みReview Seq | 変更なし | 変更なし |
| 修正開始 | `再作業中` | 変更なし | `old post-SHA` | commit確定まで`old post-SHA`保持 |
| 修正成果物commit完了 | `再レビュー待` | 変更なし | 修正開始時の値を保持 | 新成果物commit |
| 再Reviewで修正要求 | `要修正` | 新Review Seq | 変更なし | 変更なし |
| 再Review Pass | `完了` | 新Review Seq | 変更なし | 変更なし |

追加規則:

- `再レビュー待` では、最新Review targetが現artifactのancestorであることは正常状態であり、stale ReviewとしてBLOCKしない。
- `再作業中` では、直前の修正要求Reviewが最新Reviewとして残っていても `要修正` へ巻き戻さない。
- `完了` 後にcanonical artifactが更新された場合、その版は未Reviewなので `再レビュー待` へ戻す。
- `要修正 -> 再作業中` は、Workflow 00から明示された `correction_started` eventがあり、current artifact / control plane post-SHA / latest non-Pass Review targetがexact一致する場合だけ許可する。
- eventの重複実行はidempotentとし、すでに `再作業中` ならNOOPとする。
- Pass Review、stale Review、artifact更新後、対象外、未知artifactに対するcorrection startはBLOCKする。

# 5. 実行手順

## 5.1. Step 0: control plane snapshot取得

Notion connectorで `Entry_ID` に一致するlogical rowsを取得する。

logical key:

```text
(Entry_ID, 成果物)
```

各 `00 / 10 / 20` についてexact 1 rowを要求する。

取得項目:

- row/page ID
- `Status`
- `最新レビュー版`
- `pre-SHA`
- `post-SHA`
- `remarks`
- 更新競合検知に使えるlast-edited fact

duplicate / missing row / unknown Status / parse不能値はsnapshot issueとして保持し、自動補正しない。

## 5.2. Step 1: Git / Review facts取得

GitHub connectorでcurrent canonical artifactについて次を取得する。

- exists
- latest artifact commit SHA
- artifact blob SHA

Reviewについて:

```text
reviews/10_each_lore/<Entry_ID>/
```

のcanonical Review JSONを読み、

- filename / payload整合
- Review Seq
- target commit SHA
- target blob SHA
- verdict
- artifact別Review Schema

を検査してlatest Review factを作る。

malformed / duplicate / Schema invalid Reviewはsnapshot issueとして扱う。

Markdown Reviewやrendered viewは事実源にしない。

## 5.3. Step 2: SHA relation取得

GitHubのcommit graph事実から各artifactについて必要なrelationを作る。

```text
cp_post:       exact / left_ancestor / right_ancestor / diverged / missing
review_target: exact / left_ancestor / right_ancestor / diverged / missing
```

relationの意味はSection 6に従う。

LLMがcommit時刻や見た目の順序からancestryを推測してはならない。

## 5.4. Step 3: deterministic reconcile実行

connectorで得たfactsをJSON payloadへ正規化し、**current mainの `src/status_management/reconcile.py::reconcile_payload()` をPython execution environmentで実行する。**

payload概念形:

```json
{
  "controlplane": {
    "issues": [],
    "artifacts": {}
  },
  "git": {
    "artifacts": {}
  },
  "review": {
    "issues": [],
    "latest": {}
  },
  "relations": {
    "cp_post:00": "exact",
    "review_target:00": "exact"
  },
  "events": {
    "correction_started": []
  }
}
```

重要:

- state transition rulesをWorkflow Markdown側で再実装しない。
- Python環境からrepository moduleを直接importできない場合は、GitHub connectorでcurrent `reconcile.py` を取得して同一sourceを実行してよい。
- current `reconcile.py` を実行できない場合、LLM判断で代替せず `BLOCKED` とする。

reconcile結果:

- `NOOP`
- `UPDATE`
- `BLOCKED`

`BLOCKED` の場合はmutationを行わない。

## 5.5. Step 4: mutation直前の競合確認

`UPDATE` の場合、Notionを書き換える直前にmutation対象rowを再取得する。

Step 0 snapshotと以下が一致することを確認する。

- row/page ID
- Status
- 最新レビュー版
- pre-SHA
- post-SHA
- remarks
- last-edited fact

差分があれば `concurrent_update:<Artifact>` としてBLOCKし、古いmutation planを適用しない。

## 5.6. Step 5: Notion mutation適用

`reconcile_payload()` が返したmutationだけをNotion connectorで適用する。

Workflow 90が独自にStatusやSHAを追加変更してはならない。

## 5.7. Step 6: 更新後verify

mutation対象rowを再取得し、mutation planの全key/valueがexact一致することを確認する。

不一致:

```text
post_update_verification_error
```

として `ERROR`。

## 5.8. Step 7: Workflow 90結果

- reconcile=`NOOP` → `PASS`
- reconcile=`UPDATE` かつmutation + verify成功 → `UPDATED`
- reconcile=`BLOCKED` または競合検知 → `BLOCKED`
- connector / parse / write / verify実行不能 → `ERROR`

`PASS / UPDATED` の場合のみ呼出元Workflowは後続処理へ進める。

## 5.9. optional external adapter

```text
python -m src.status_management.sync_controlplane <Entry_ID>
```

は削除しない。

ただしこれは:

- Notion Public API tokenを持つbatch / CI / external runtime

向けのoptional adapterであり、本番チャットWorkflow 00/90の必須経路ではない。

adapterも内部では同じ `reconcile.py` を使用しなければならない。

# 6. SHA関係の解釈

- `exact`: 対象版一致。
- control plane `post-SHA` が現artifact SHAのancestor: control planeが古い。事実から一意に更新可能ならpre/postを前進させる。
- Review対象SHAが現artifact SHAのancestor:
  - `再レビュー待` または修正commit直後であれば正常。
  - その他の状態ではstale ReviewとしてBLOCKする。
- 現artifact SHAがReview対象SHAのancestor: Review target aheadとしてBLOCKする。
- `diverged`: 自動修復せず調査対象。
- Review成果物自身のcommitをcanonical artifactの `post-SHA` として扱わない。

# 7. Review結果の保存先

Review結果JSONは以下を事実源とする。

```text
reviews/10_each_lore/<Entry_ID>/
└─ Review_<Entry_ID>_<Artifact>_<Review_Seq>.json
```

Schema対応:

```text
Artifact 00 -> review_00_sources.schema.json
Artifact 10 -> review_10_contents.schema.json
Artifact 20 -> review_20_analysis.schema.json
```

- Markdown derived viewは同期事実源として使用しない。
- 「最新Review」はmtimeではなくReview Seqを基準とする。
- artifactとSchemaが不一致のReview JSONはmalformedとして扱い、自動同期の事実源にしない。

# 8. Workflowからの呼出し

- Workflow 10は作業開始前、canonical artifact commit後、Review修正後、完了時に必要に応じWorkflow 90を呼ぶ。
- Workflow 20はcontrol planeを直接更新せず、必要な整合確認をWorkflow 90へ委譲する。

# 9. 不変条件

- current stateはNotionに保持する。
- Notion stateはGit / Review事実より優先しない。
- Status enumはNotion、Workflow 90、`reconcile.py` で一致させる。
- **state transition / fail-stop / mutation planは `reconcile.py` を唯一の正本とする。**
- connectorはI/O adapterであり、state transition ruleを持たない。
- 同期はidempotentであること。
- 不明状態を推測で正常化しないこと。
- duplicate、malformed Review、divergence、concurrent update等の曖昧状態では自動更新しないこと。
- mutation直前の再読と更新後verifyを省略しないこと。
- control planeからEvidence内容やD01〜D21妥当性を推定しないこと。

# 10. correction start event

`要修正 -> 再作業中` の未確定事項は解消済みとする。

発生条件:

1. ユーザーがWorkflow 00 + Entry_IDで本番E2E継続を明示依頼している。
2. Workflow 00が `CORRECTION_REQUIRED` を確認する。
3. Workflow 00が実際にWorkflow 10 correction phaseへ入る。
4. その時点で対象artifactに `correction_started` eventを発行する。
5. `reconcile.py` がcurrent artifact / control plane / non-Pass Reviewのexact一致を検証する。

この5条件を満たした場合だけ `再作業中` へ遷移する。

