# Schema v2 contract

v2はTask 17で確定したcanonical domain modelを実装する。

## Identity

- `investigation_id`: `INV-NNNNNN`
- `rq_id`: `RQ-NNNN`
- Investigation IDはRQ IDをencodeしない。
- 1つのartifact chainでは全artifactの `investigation_id` と `rq_id` が一致しなければならない。
- `00_context` はResearch Context entityではなく **Investigation Context** である。

## Compatibility

- 新規Investigationはv2を使用する。
- `schemas/v1` は既存 `RQ-NNNN-vVVV` historical artifactのlegacy validationにのみ使用する。
- v1 artifactをv2へin-place rewrite / renameしない。

Task 17ではidentity semanticsを修正するため、Evidence / Synthesis / Analysisのsemantic structureはv1から必要以上に変更しない。


## Projection provenance

BKL-0025以降のWorking Answer body projection provenanceは `projection_log.schema.json` を使用する。

- targetはResearch Question page bodyの `# Working Answer` section。
- historical property projectionの `projection_log.json` はrewriteしない。
- new body projectionはInvestigation directoryの `projection_log_v2.json` として記録する。


## Review schema selection — current vs deprecated

**New Workflow 20 Review cycles MUST NOT use** the following deprecated compatibility paths:

- `review_common.schema.json`
- `review_cycle.schema.json`

These names remain only for historical compatibility and are explicitly marked `deprecated: true`. Their legacy implementations live under `schemas/v2/legacy/`.

For a new split Review cycle, the current schema set is:

- `review_layer_common.schema.json`
- `review_manifest.schema.json`
- `review_00_context.schema.json`
- `review_10_evidence.schema.json`
- `review_20_synthesis.schema.json`
- `review_30_analysis.schema.json`

Human researchers and LLM executors should treat any instruction to author a new Review against `review_cycle.schema.json` or `review_common.schema.json` as stale.

## Semantic Review persistence

BKL-0034以降、新規Workflow 20 Review Cycleは **cycle manifest + 4 layer Review JSON** としてappend-only保存する。

```text
investigations/<Investigation ID>/reviews/
  review-<Review Seq: 6 digits>.json
  review_00_<Review Seq: 6 digits>.json
  review_10_<Review Seq: 6 digits>.json
  review_20_<Review Seq: 6 digits>.json
  review_30_<Review Seq: 6 digits>.json
```

- Review cycle identityは `(Investigation ID, Review Seq)`。
- `review-XXXXXX.json` はcycle manifestであり、target commit / 4 artifact blob SHA、reviewed_at、layer file references、cycle verdictを保持する。
- `review_00 / 10 / 20 / 30` は各semantic review layerのcanonical assessmentを保持する。
- `review_manifest.schema.json` がnew split cycle manifest schema。
- `review_00_context.schema.json / review_10_evidence.schema.json / review_20_synthesis.schema.json / review_30_analysis.schema.json` がlayer schema。
- `review_layer_common.schema.json` はFinding / severity / repair direction / SHA / verdict等の**current**共通型定義。
- layer verdictは各layerのFinding集合から、cycle verdictは4 layer Finding集合のunionからdeterministically算出する。
- Finding IDはReview Cycle全体で `F001...` の連番とし、logical identityは `(Investigation ID, Review Seq, Finding ID)`。
- manifestと4 layer fileはInvestigation ID / Review Seq / target blob SHA / filename / verdict consistencyをloaderが検証する。
- missing / orphan / malformed layer fileやReview Seq gapはfail-stopする。
- Markdown等のReview viewはderivedでありcanonical factではない。

### Legacy compatibility

BKL-0034以前のcanonical `review-XXXXXX.json` はhistorical single-file Review Cycleとしてin-place rewriteしない。

- legacy `report_type = semantic_review` はdeprecated compatibility path `review_cycle.schema.json`（実体: `legacy/review_cycle.schema.json`）で継続validationする。
- new split cycleは `report_type = semantic_review_manifest` + 4 layer filesを使用する。
- history loaderはlegacy / split双方をstorage-neutral normalized Review Cycleへ変換する。
- `schemas/v3` は作成せず、compatibilityを `schemas/v2` 内で管理する。
