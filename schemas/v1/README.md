# Schema v1 contract

> **Legacy compatibility contract.** 新規Investigationには使用しない。既存 `RQ-NNNN-vVVV` historical artifactの再検証専用として凍結する。新規canonical artifactは `schemas/v2` を使用する。

このdirectoryには、Research Atelier artifactに対するcanonical JSON Schema Draft 2020-12 contractを置く。

## Policy

- `schema_version` はrequiredとし、各schema revisionで `const` により固定する。
- `artifact_type`、`investigation_id`、`rq_id` はrequired identity fieldとする。
- ID formatは `docs/00_management/0002_investigation_versioning.md` を正とする。
- `investigation_id` のRQ prefixと `rq_id` の一致など、standard JSON Schemaだけでは表現しにくいcross-field invariantはdeterministic Python validatorで検査する。
- canonical artifact objectでは `additionalProperties: false` を基本とし、accidental fieldが暗黙にcontractへ入ることを防ぐ。
- `required` にはartifact identityとminimum semanticsを維持するために必要なfieldだけを置く。
- unknownはschemaが許す範囲で省略または明示的 `null` とする。空文字、`TBD`、架空defaultをcanonical unknown valueとして使わない。
- `enum` はQuestion Type、context state、Evidence Note type、Synthesis relation typeなど、architectureですでにclosed vocabularyとして定義されたものに限定して使う。
- Schema validationが保証するのはstructural validityであり、semantic truthではない。Evidence-faithfulnessやanalytical correctnessにはdeterministic lineage checkとsemantic reviewが必要である。

## 00_context

`00_context.schema.json` はincompleteなdraft Research Contextを許容する。

Scope、Significance、Question Typeはunknownでもよい。

frozen contextでは `frozen_at` をrequiredとする。

## 10_evidence

`10_evidence.schema.json` はInvestigation-specificなEvidence snapshotを保持する。

各evidence itemはSource provenanceを保持し、Evidence Noteが存在する場合はそのreferenceも保持する。

direct Source snapshotの場合、`evidence_note` はnullでよい。

Evidence Noteについてv1では、source-faithful note text、`Note Type`、`Location`、`Direct Quote` をfreezeできる。

Sourceのbibliographic metadataはNotion-authoritativeのままとし、Investigation artifactへ一式copyしない。

このschemaにはWorking Answerやanalysis judgment fieldを置かない。

## 20_synthesis

`20_synthesis.schema.json` はEvidence-faithfulなknowledge unitを保持する。

各knowledge unitはstableな `knowledge_unit_id` と1件以上の `evidence_refs` を持つ。

knowledge unit間のagreement / conflictは `relations[].relation_type` で表し、uncertaintyは `uncertainties` collectionで明示する。

Working Answerはこのartifactではinvalidである。

## 30_analysis

`30_analysis.schema.json` は、RQ-specific analytical judgmentを初めて保持するschemaである。

common fieldには以下を含む。

- Working Answer
- analytical judgment
- limitation
- unresolved question
- optional alternative interpretation
- `knowledge_unit_refs` によるSynthesisへのlineage

analytical judgmentにはraw `evidence_refs` を置かない。

Evidence lineageはtransitiveに次の形を取る。

`30_analysis -> knowledge_unit_ref -> 20_synthesis.evidence_refs -> 10_evidence`

### Question Type-specific profile

`question_type` はconditional JSON Schema branchを通じてrequired `profile` objectを選択する。

8 profileの定義は `docs/00_management/0009_analysis_profiles.md` を正とする。

- Exploratory
- Descriptive
- Comparative
- Causal
- Mechanistic
- Predictive
- Methodological
- Conceptual

profile fieldはstructurally type-specificとする一方、unknownを捏造して埋める必要がないよう、適切なfieldはoptional / nullableとする。

`additionalProperties: false` により、異なるsemantic profileのfieldが混入することを防ぐ。

## Fixtures

fixtureは `tests/fixtures/v1` に置く。

- `*.valid.min.json` は対応schemaをPASSしなければならない。
- `*.invalid.*.json` はfile名で示したreasonによりFAILしなければならない。

`src/research_atelier/validation` のdeterministic validatorは、JSON Schemaに加えてcross-artifact identity、duplicate ID、lineage reference、staged validationを検査する。
