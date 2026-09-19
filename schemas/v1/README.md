# Schema v1 contract

本directoryには、Research Atelier artifactのcanonical JSON Schema Draft 2020-12 contractを置く。

## Policy

- `schema_version` はrequiredであり、各schema revisionで `const` により固定する。
- `artifact_type`、`investigation_id`、`rq_id` はrequired identity fieldとする。
- ID formatは `docs/00_management/0002_investigation_versioning.md` を正とする。
- `investigation_id` のRQ prefixと `rq_id` の一致など、JSON Schemaだけでは表現しにくいcross-field invariantはdeterministic Python validatorで検査する。
- canonical artifact objectは原則 `additionalProperties: false` とし、accidental fieldが暗黙にcontractへ入ることを防ぐ。
- `required` はartifact identityとminimum semanticsを保つために必要なfieldだけに絞る。
- unknownはSchemaが許す範囲で省略または明示的 `null` とする。空文字、`TBD`、架空defaultはcanonical unknown valueとして使わない。
- `enum` はQuestion Type、context state、Evidence Note type、Synthesis relation typeなど、architecture上closed vocabularyと定義したものに限定する。
- Schema validationが保証するのはstructural validityであり、semantic truthではない。Evidence-faithfulnessやanalytical correctnessにはdeterministic lineage checkとsemantic reviewが必要である。

## 00_context

`00_context.schema.json` はincompleteなdraft Research Contextを許容する。

Scope、Significance、Question Typeはunknownでもよい。

frozen contextでは `frozen_at` をrequiredとする。

## 10_evidence

`10_evidence.schema.json` はInvestigation-specific Evidence snapshotを保存する。

各Evidence itemはSource provenanceを保持し、Evidence Noteが存在する場合はそのreferenceも保持する。Source recordを直接snapshotした場合は `evidence_note = null` を許容する。

Evidence Noteについて、v1ではsource-faithful note text、`Note Type`、`Location`、`Direct Quote` をfreezeできる。

Source bibliographic metadata全体はNotion-authoritativeのままとし、Investigation artifactへ一式copyしない。

Working Answerやanalysis judgment fieldは意図的に持たせない。

## 20_synthesis

`20_synthesis.schema.json` はevidence-faithful knowledge unitを保存する。

各knowledge unitはstable `knowledge_unit_id` と1件以上の `evidence_refs` を持つ。

Evidence間agreement / conflictは `relations[].relation_type` で表現し、uncertaintyは `uncertainties` collectionで明示する。

Working Answerはこのartifactではinvalidとする。

## 30_analysis

`30_analysis.schema.json` はRQ-specific analytical judgmentを初めて保持するschemaである。

common field:

- Working Answer
- analytical judgment
- limitation
- unresolved question
- optional alternative interpretation
- `knowledge_unit_refs` によるSynthesis lineage

analytical judgmentへraw `evidence_refs` を持たせない。

Evidence lineageはtransitiveとする。

`30_analysis -> knowledge_unit_ref -> 20_synthesis.evidence_refs -> 10_evidence`

これによりAnalysisからSynthesisをbypassすることを防ぐ。

### Question Type-specific profile

`question_type` はconditional JSON Schema branchによりrequired `profile` objectを選択する。

8 profileは `docs/00_management/0009_analysis_profiles.md` で定義する。

- Exploratory
- Descriptive
- Comparative
- Causal
- Mechanistic
- Predictive
- Methodological
- Conceptual

profile fieldはType-specificである一方、unknownを架空値で埋めなくてよいよう、必要に応じてoptional / nullableとする。

各profileで `additionalProperties: false` を使い、異なるsemantic profileのfield混入を防ぐ。

## Fixtures

fixtureは `tests/fixtures/v1` に置く。

- `*.valid.min.json` は対応schemaをPASSしなければならない。
- `*.invalid.*.json` はfile名で示した理由によりFAILしなければならない。

`src/research_atelier/validation` のdeterministic validatorは、JSON Schemaに加えてcross-artifact identity、duplicate ID、lineage reference、staged validationを検査する。
