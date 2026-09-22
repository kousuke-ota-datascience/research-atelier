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
