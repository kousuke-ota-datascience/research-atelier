# 0. 位置付け

本書は、現行の本番Entry Pipelineを**既存canonical / Legacy / 過去Reviewから意味論的に隔離した状態で検証するE2E Test Protocol**の正本である。

本書は00→10→20→Reviewの業務ロジックを再実装しない。

- production orchestration: `0000_workflow_00_entry_pipeline.md`
- canonical生成・修正: `0000_workflow_10_each_lore_analysis.md`
- semantic Review: `0000_workflow_20_review.md`
- control plane同期: `0000_workflow_90_sync_controlplane.md`

E2E Testは上記と同じ意味論を、isolated candidate環境で実行する。

# 1. 目的

E2E Testで確認するのは、過去成果物との一致ではなく、**現行Workflow / Schema / taxonomy / validation / Review contractだけから、Entryを00→10→20→Reviewまで一貫して処理できること**である。

特に次を検証する。

1. Legacyやexisting canonicalを見なくてもEvidenceからcanonicalを生成できる。
2. 00→10→20の依存関係が守られる。
3. summaryがsalient meaningを保持する。
4. Reviewがcurrent candidateだけを対象に独立判定できる。
5. deterministic validation / Review writer / state invariantsが成立する。
6. 差分比較を行っても、その差分が生成過程へ逆流しない。

# 2. 入力

通常入力は:

```text
Entry_ID または Entry_ID[]
```

対象Entry名はEntry_ID解決の補助として使用してよい。

# 3. Blind Phaseで参照禁止のもの

candidate freezeまでは、次を意味論的期待値として参照してはならない。

- `docs/legacy/`
- Legacy Review
- 旧Excel
- existing canonical 00 / 10 / 20
- existing canonicalを基にしたrendered Markdown
- 過去Review JSON
- 過去Golden Reference
- Legacyまたはexisting canonicalから作った「残すべき意味」一覧
- historical Content ID / Evidence ID / variant ID
- historical taxonomy codeを「一致すべき正解」とした期待値

リポジトリ内に物理的に存在すること自体は失格条件ではない。**生成・Review判断へ使用しないこと**が契約である。

# 4. 参照可能なもの

Blind Phaseで使用してよいもの:

- 現行Workflow 00 / 10 / 20 / 90
- 現行JSON Schema
- 現行taxonomy catalog / coding rules
- 現行validation実装
- 外部一次・二次資料
- Entry registry等、Entry_ID解決に必要な非意味論的管理情報

# 5. isolated candidate環境

E2E Testはproduction canonicalを直接上書きしない。

推奨:

```text
main
  └─ isolated E2E branch / candidate workspace
       ├─ candidate 00
       ├─ candidate 10
       ├─ candidate 20
       └─ candidate Review
```

Blind Phase中は:

- production Notion stateを更新しない。
- existing Review historyへcandidate Reviewを混入しない。
- candidate artifactをmain canonicalとして扱わない。

# 6. 実行Phase

## 6.1. Phase A: Blind Generation

外部資料から独立に:

```text
00_sources
    ↓
10_contents
    ↓
20_analysis
```

を生成する。

Workflow 10の意味論をそのまま使用する。

特に10 Contentsでは、流通史・社会反応・書誌事実を無条件にContent Unit化せず、伝承内部の人物・出来事・規則・作用・終端・variant差を中心に再構成する。

## 6.2. Phase B: Deterministic Validation

各candidateを現行validationで検査する。

```text
00 validation
10 validation
20 validation
```

Schema / reference / taxonomy errorが残った状態でReviewへ進まない。

## 6.3. Phase C: Blind Semantic Review

candidate 00 / 10 / 20だけを対象としてWorkflow 20を実行する。

禁止:

- existing Reviewを見て同じFindingを再現すること
- Legacy Reviewを正答として使うこと
- existing canonicalとの差分を見てからReview verdictを決めること

Review 10では、Blind Decodeを先に行い、その後に`summary.coverage_refs`の全件auditを行う。

## 6.4. Phase D: Freeze

以下をfreezeする。

- candidate 00 commit / blob
- candidate 10 commit / blob
- candidate 20 commit / blob
- candidate Review cycle
- validation result
- Review verdict

**Freeze前にexisting canonical / Legacyとの差分比較を行わない。**

# 7. Differential Audit

Freeze後に初めて、candidateを以下と比較してよい。

- existing canonical
- Legacy
- historical Review

差分は少なくとも次へ分類する。

| Class | 定義 |
|---|---|
| `NEW_SYSTEM_FIX` | candidate側の欠落・誤り |
| `OLD_CANONICAL_DEFECT` | existing canonical側の欠陥 |
| `LEGACY_DEFECT` | Legacy側の欠陥 |
| `NORMALIZATION` | Schema / taxonomy /表現方式の正規化 |
| `REPRESENTATION_ONLY` | 意味不変の分割・ID・表現差 |
| `INVESTIGATE` | 根拠不足で分類不能 |

差分を見つけても、freeze済みcandidateを黙って書き換えて「元からPASSだった」と扱わない。

candidate修正が必要なら、**post-freeze correction cycle**として履歴を分ける。

# 8. Regression contract

回帰テストはhistorical IDへ意味を固定しない。

禁止例:

```text
CNT-009に兄の終端がなければFAIL
```

許可例:

```text
兄が白い存在と同様にくねくね動くsalient Content Unitが存在し、
そのContent IDがsummary.coverage_refsに含まれること
```

つまり比較対象は:

- salient meaning
- coverage contract
- Schema contract
- causal / variant / uncertainty invariants

であり、次ではない。

- Content ID
- unit順序
- historical split
- historical wording

# 9. Promotion

candidateをmainへpromotionする条件:

1. 00 / 10 / 20 validation PASS。
2. candidate Review 00 / 10 / 20が全てPass。
3. freeze後差分監査が完了。
4. `INVESTIGATE` の未解消差分がproduction correctnessに影響しない、または解消済み。
5. promotion対象が明示されている。
6. promotion後に本番Workflow 90でcontrol planeを収束可能。

promotion後はcandidate Reviewをそのまま「既存main artifactへのReview」とみなさず、target commit / blob一致を検査する。

# 10. E2E Testの成功条件

E2E TestのPASSは次を意味する。

```text
BLIND_GENERATION_COMPLETED
AND
VALID(candidate 00 / 10 / 20)
AND
BLIND_REVIEW(00 / 10 / 20) == Pass
AND
CANDIDATE_FROZEN_BEFORE_DIFF
AND
NO_SEMANTIC_EXPECTATION_LEAKAGE
AND
DIFFERENTIAL_AUDIT_COMPLETED
```

existing canonicalとの一致率やLegacy再現率はPASS条件ではない。

# 11. 本番Workflowとの関係

E2E Test専用の00→10→20実装を作らない。

```text
Workflow 00
    ├─ Production
    │    └─ main canonical + production control plane
    │
    └─ E2E Test Protocol
         └─ isolated candidate + no production mutation before promotion
```

E2E Testで発見したWorkflow defectは、test-only workaroundではなく本番Workflow / Schema / validationへ戻して修正する。

# 12. 記録

E2E記録には最低限以下を残す。

- Entry_ID
- candidate branch / workspace
- 00 / 10 / 20 commit / blob
- validation result
- Review Seq / verdict
- freeze時点
- differential classification
- correction cycleの有無
- promotion結果
- discovered workflow / schema / test defects

# 13. 不変条件

- BlindとDifferential Auditを混ぜない。
- Legacyをexpected outputとして扱わない。
- existing canonicalをexpected outputとして扱わない。
- Reviewはcandidateだけを見て判定する。
- ID一致をmeaning preservationの代替にしない。
- production stateへ副作用を出すのはpromotion後だけ。
- 差分起因の修正は別cycleとして記録する。
