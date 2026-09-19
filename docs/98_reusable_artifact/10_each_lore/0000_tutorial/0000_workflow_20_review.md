# 0. ドキュメント情報

## 0.1. 位置付け

本書は、canonical artifactに対する独立意味論Reviewの正本である。

## 0.2. 設計原則

- Reviewerはcanonical artifactを直接修正しない。
- ReviewerはNotion control planeを直接更新しない。
- Schema / deterministic invariantの検査はPythonへ委譲し、Reviewは意味論に集中する。
- Review対象版は開始時にcommit SHA / blob SHAで固定する。
- 過去Review・旧Excel・既存コードを正解としてReviewしない。
- Review結果の正本はGit上のJSONとする。
- canonical JSONの構造を、そのartifactで確認すべきReview観点の母集団とする。
- Review JSONのartifact固有Schemaに定義された必須check・監査証跡を省略しない。

# 1. 目的と責務

## 1.1. 目的

`00_sources.json → 10_contents.json → 20_analysis.json` の連鎖について、EvidenceからContentへの再構成とContentからAnalysisへの判断が意味論的に妥当かを独立に評価する。

## 1.2. 担う責務

- Source / Evidenceの品質・関係・最古確認・不確実性を確認する。
- EvidenceがContentを支持しているか確認する。
- summaryの情報保存性・再構成可能性を確認する。
- 初期形、後代異伝、最古確認、起源の区別を確認する。
- Version Scopeの妥当性を確認する。
- `macro_category / entry_type` がEntry内容と整合するか確認する。
- D01〜D21の意味論的妥当性を確認する。
- sense-making / 因果構造の整合を確認する。
- semantic traceabilityを確認する。
- Findingを根拠・影響・修正方向とともに記録する。

## 1.3. 担わない責務

- JSON Schema validation。
- required field / ID重複 / cross-reference / Parent-Child等の機械的検査。
- control planeの同期・修復。
- Review対象artifactの修正。

# 2. インターフェイス

## 2.1. 入力

- 原則 `Entry_ID` のみ。
- Review開始時に対象Entryのcanonical artifactと対象SHA / blobを内部で固定する。

## 2.2. 出力

- Review結果の正本はGit上のJSONとする。
- 保存先は `reviews/10_each_lore/<Entry_ID>/` とする。
- 1成果物につき1 Review結果ファイルを生成する。
- 命名は `Review_<Entry_ID>_<Artifact>_<Review_Seq>.json` とする。
- `Artifact` は `00 / 10 / 20` のいずれか。
- 同一Review cycleでは対象artifact間で同じ `Review_Seq` を共有する。
- Review JSONはartifactに応じて次のSchemaに準拠する。

```text
Review_<Entry_ID>_00_<Review_Seq>.json -> schemas/review_00_sources.schema.json
Review_<Entry_ID>_10_<Review_Seq>.json -> schemas/review_10_contents.schema.json
Review_<Entry_ID>_20_<Review_Seq>.json -> schemas/review_20_analysis.schema.json
```

- `schemas/review_common.schema.json` は共通 `$defs` のみを提供し、単独のReview validation targetにはしない。
- Review JSONからMarkdown viewを生成する処理はReview cycleの必須工程に含めない。
- 人から明示的な変換指示があった場合のみ `src/rendering/render_review.py` を実行する。
- 生成Markdownはderived viewであり、Review完了条件・Verdict・control plane状態には影響しない。
- 旧Review JSONを上書きせずappend-onlyで追加する。
- Review Seq採番、対象SHA / blob固定、Verdict集約、save-time Schema validation、append-only書込は `src/reviewing/review_writer.py` に委譲する。
- Reviewerが作成するのはartifact固有のsemantic bodyのみとし、`schema_version / entry_id / artifact / review_seq / target / verdict` はPythonが付与する。

# 3. Review開始条件

- 対象canonical artifactをGit上で一意に固定できること。
- `python -m src.validation.validate_entry <Entry_ID>` がPASSしていること。
- Workflow 90により、Review対象版を阻害するcontrol plane不整合がないこと。
- Review開始時に内部処理として `python -m src.reviewing.review_writer prepare <Entry_ID>` を実行し、00 / 10 / 20の対象commit SHA / blob SHAと次の共有 `Review_Seq` をcycle snapshotとして固定する。
- prepare時点でcanonical artifactに未commit差分がある、既存Review履歴がSchema不正・不完全cycleである、対象SHA / blobを固定できない場合はfail-stopとする。
- semantic Review中はprepareで得たcycle snapshotを保持し、対象版を後から読み替えない。

# 4. Review 10: Summary Reconstruction Review

## 4.1. Blind Decode

- `10_contents.json` の `summary.narrative + summary.structure` だけを入力として、**伝承そのものの具体的展開**を再構成する。
- Blind Decode中は `summary.coverage_refs` のID列、`content_units / variants / uncertainties`、Evidenceを参照しない。ID列を見てReference Storyを推測してはならない。
- 再構成はAnalysis用抽象概念に縮約せず、「誰／何に、具体的に何が起き、どう変化し、どう終わるか」を記述する。
- transformation、identity change、terminal scene、motif echoがsummaryに存在する場合は、具体的意味として再構成する。

## 4.2. Salient Coverage Audit

- Blind Decode完了後に初めて `summary.coverage_refs` を読む。
- 各 `coverage_ref` が指すContent unitを1件ずつ確認し、そのsalient meaningがBlind Decodeから復元できたかを監査する。
- 各refについて `content_ref / salient_meaning / blind_reconstruction / difference` を記録する。
- `difference` は `NONE / LOSS / CONFLICT` とする。
- **Analysisを再構成できるかどうかとは独立に判定する。** 分析コードが同じでも、具体的終端、transformation、identity、motif echo、variantを決める出来事がsummaryから失われていれば `LOSS` とする。
- Evidence上の留保がsummaryで強められた場合（例: 「怪異と同様に動く」→「怪異そのものへ変身した」）は `CONFLICT` とする。
- `coverage_refs` の全件が監査対象であり、人手で別のアンカー集合を後から選んで代替してはならない。

## 4.3. Reference Story

- Coverage Audit後に `content_units / variants / uncertainties` と必要なEvidenceを参照し、基準となるReference Storyを再構成する。
- Reference Storyは `coverage_refs` のsalient meaningをすべて含み、必要な不確実性・variant境界も保持する。

## 4.4. Structural Probe

少なくとも以下をP01〜P12として全件確認する。

- P01 primary actors / roles
- P02 affected targets
- P03 trigger / entry
- P04 cause / agent
- P05 mechanism / action
- P06 state transition
- P07 order / repetition / delay / continuation
- P08 conditions / rules / taboos
- P09 avoidance / control / use
- P10 terminal state
- P11 unresolved / unknown
- P12 initial / later / major variant boundaries

## 4.5. 二層判定

Review 10では次を独立判定する。

1. **Narrative Reconstruction** — summaryだけから伝承の具体的展開を再構成できるか。
2. **Analysis Reconstruction / Invariance** — summaryから後続Analysisに必要な構造を再構成できるか。

- Narrative Reconstructionでsalient unitに `LOSS / CONFLICT` がある場合、Analysis ReconstructionがPASSでもsummary ReviewはPASSにしない。
- 「重大な異変」「危害」「変容」等の抽象語だけでAnalysis codeを再構成できても、Contentで重要な具体的終端・identity変化・怪異との類似が消えている場合はFindingとする。

## 4.6. 比較と保存

- Blind DecodeとReference Storyを比較する。
- `Review_*_10_*.json` には、従来の `blind_decode / reference_story / probes[P01-P12] / analysis_invariance / verdict` に加えて、`coverage_audit` を保存する。
- `checks.narrative_reconstruction` は具体的伝承再構成、`checks.summary_reconstruction` はsummary全体の再構成性、`checks.structural_probe` はP01〜P12の状態を表す。
- 新契約の `summary.coverage_refs` を持つ対象では、`coverage_audit` はcoverage refsと完全一致しなければならない。
- `coverage_audit` に `LOSS / CONFLICT` が1件でもある場合、`reconstruction.verdict` は `FINDING` とし、対応Findingを残す。

# 5. Review 00 / 10: Evidence・Content Review

## 5.1. Review 00

- Source種別・資料同定・参照位置が妥当か。
- SourceとEvidenceの対応、quote / paraphraseの扱いが妥当か。
- 一次資料との関係を誤認していないか。
- 「最古確認」と「実際の起源」を混同していないか。
- 一次未発見、二次のみ、競合、後代付加可能性、確認不能等の不確実性を保持しているか。

## 5.2. Review 10

- Content主張が参照Evidenceによって実際に支持されるか。
- 後代設定を初期形へ遡及していないか。
- 不明・資料間競合・確認不能を不当に閉じていないか。
- Content層へAnalysis判断が混入していないか。
- variant境界がEvidenceと整合するか。

# 6. Review 20: Content → Analysis Review

## 6.1. 基本Review

- `macro_category / entry_type` がEntryのContentと意味論的に整合するか。
- Version ScopeがEvidence / Contentに照らして妥当か。
- D01〜D21の判定がcoding rulesとContentに整合するか。
- rationaleが参照Contentを実際に支持しているか。
- manifestationがコード定義の言い換えではなくEntry固有の記述か。
- `D / I / U / NA / C` のstatus理由がEvidenceに即しているか。
- taxonomy gapを不適切に既存コードへ押し込めていないか。

## 6.2. 必須Critical checks

以下は一般的なDimension Reviewへ埋没させず、`Review_*_20_*.json` の個別必須checkとして全件記録する。

- `d12_d13_d15_causal_chain`: D12作用対象 → D13作用・機序 → D15帰結の因果列がContentと整合するか。
- `d18_scope_independent_x_evidence`: D18でL3相当を選ぶ場合、Version Scope内に独立したX Evidenceがあるか。
- `d19_publicability_vs_national_distribution`: 公開可能性・公開媒体の存在を全国流通と誤同一視していないか。
- `d20_missing_info_vs_no_one_knows`: 情報が確認できないことを `NO_ONE_KNOWS` と誤同一視していないか。
- `d21_reality_anchor`: Evidence資料の実在性とScoped Content内の現実アンカーを混同していないか。
- `evidence_confidence_ceiling`: Analysisの確信度がEvidence / Contentの支持強度を超えていないか。
- `entry_classification`: `macro_category / entry_type` がEntry内容と整合するか。

## 6.3. Sense-making再構成

- 20_analysisの判定を読むだけで済ませず、Reviewer自身がContentから意味形成・因果モデルを再構成する。
- `Review_*_20_*.json` の必須 `sensemaking_reconstruction` に、`model / content_refs / dimension_refs / status` を保存する。
- Contentだけでは監査不能な場合のみ補助的に `evidence_refs` を持たせる。
- 再構成結果は新たなcanonical Analysisではなく、20_analysisの意味論を検証した監査証跡である。

# 7. Analysis Invariance

- original Evidence / Contentを読む場合とsummaryを読む場合で、主要分析可能性が実質的に変化していないか確認する。
- 少なくともD07〜D10、D11、D12、D13、D14、D15、D16、D17、D18、D19〜D20、D21、Version Scope / variant boundaryへの影響を確認する。
- Review 10の `reconstruction.analysis_invariance` とReview 20の `checks.analysis_invariance` を監査証跡として残す。

# 8. FindingとVerdict

## 8.1. Finding

- Findingは対象artifactのReview Schemaに従う。
- Review 00は `review_00_sources.schema.json`、Review 10は `review_10_contents.schema.json`、Review 20は `review_20_analysis.schema.json` を正とする。
- 各Findingは対象箇所、根拠、影響、修正方向を持つ。
- Finding severityは `Minor / Moderate / Major` とする。
- checks / reconstructionの全内容をFindingへ複製せず、修正が必要な単位だけをFinding化する。

## 8.2. Verdict

VerdictはFinding集合から決定論的に再計算可能でなければならない。

- Findingなし: `Pass`
- Minorのみ: `Minor`
- Moderateが1件以上かつMajorなし: `Moderate`
- Majorが1件以上: `Major`

ReviewerはFindingの意味論的内容を記述し、独自ルールでVerdictを手計算しない。

# 9. Review保存と再Review

- 00 / 10 / 20のsemantic Reviewが完了したら、prepareで得た `cycle` と3 artifactのsemantic bodyを1つのJSON bundleとして `python -m src.reviewing.review_writer write <Entry_ID>` のstdinへ渡す。
- writerは保存直前に、Entry validation PASS、次Seq、対象commit/blob、working tree一致を再確認する。prepare後にartifact更新または別Review cycleの追加があれば保存せずERRORとする。
- writerは3 artifactを同一 `Review_Seq` で一括validationし、3ファイルすべてが有効な場合だけappend-onlyで保存する。
- 保存後、当該3 Review JSONだけを1つのReview cycle commitとしてcommit / pushする。
- push後にWorkflow 90を実行してcontrol planeを同期する。
- 修正後の再Reviewでは再度prepareを行い、新しい対象SHA / blobと新Review Seqを固定する。
- Review JSON作成・再Review時にMarkdownを自動生成しない。
- Markdown viewが必要な場合は、人からの明示指示を受けて `render_review.py` を個別実行する。
- 旧Reviewを上書きしない。
- stale Review判定・control plane収束はWorkflow 90 / `sync_controlplane.py` へ委譲する。
- Workflow 20から `notion_controlplane.py` / `git_state.py` / `review_state.py` / `reconcile.py` を直接呼び出さず、Review write側のdeterministic処理は `review_writer.py` の公開入口だけを使用する。

# 10. Review結果の監査不変条件

- Review JSONは特定のcanonical artifact commit SHA / blob SHAを対象とする。
- Review結果ファイル自身を追加したcommit SHAを対象artifactのSHAとして扱わない。
- 同一 `(Entry_ID, Artifact, Review_Seq)` を上書きしない。
- Review本文・Finding・Verdictの正本はJSONであり、derived Markdownではない。
- artifactとReview Schemaの対応を取り違えない。
- Review Schemaが必須化したcheck / reconstructionを省略してPass扱いにしない。

# 11. deterministic Review write実装

- 実装: `src/reviewing/review_writer.py`
- prepare: `python -m src.reviewing.review_writer prepare <Entry_ID>`
- write: `python -m src.reviewing.review_writer write <Entry_ID>`。入力bundleはstdinから受ける。
- Review Seqは既存canonical Review JSONの全artifact共通最大Seq + 1とする。
- 既存cycleが00 / 10 / 20のexact setでない場合、新規Seqを採番せずfail-stopする。
- writeは00 / 10 / 20のexact setを1単位とし、一部artifactだけを新cycleとして保存しない。
- filenameは `Review_<Entry_ID>_<Artifact>_<Review_Seq:03d>.json` とする。
- 既存destinationが存在する場合は上書きせずERRORとする。
- save-time Schema validationには `src.validation.schema_validator.validate_data` を使用する。
- `src/status_management/review_state.py` は引き続きread-onlyとし、write責務を追加しない。
