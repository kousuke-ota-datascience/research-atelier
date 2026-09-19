# Question Type別 Analysis Profile

## 目的

`30_analysis` は、全Question Type共通のanalysis fieldと、`question_type` が選択するType-specific `profile` から構成する。

これによりDescriptive / Causal / Predictive / Mechanistic等、意味論の異なる判断を同じfieldとして混在させない。

## 共通field

以下はprofile外に置き、全Question Typeで同じ意味を持つ。

- `working_answer`
- `judgments`
- `limitations`
- `unresolved_questions`
- `alternative_interpretations`
- `knowledge_unit_refs` によるlineage

profileはanalysis setupを構造化するためのものであり、final conclusionを重複記録しない。

## Unknown / not applicable

Type-specific fieldは、将来method-specific contractが必須化しない限りoptionalを基本とする。

unknownはSchemaが許す範囲で省略、`null`、空collectionとして表す。

missing fieldは0、false、no effect、not applicableを意味しない。値が不明なのに埋めてはならない。

## Exploratory

Fields:

- `patterns`
- `candidate_hypotheses`
- `anomalies`
- `evidence_gaps`

pattern discovery / hypothesis generationへ用いる。

candidate hypothesisを確立済みcausal conclusionとして扱わない。

## Descriptive

Fields:

- `target`
- `constructs`
- `summary_statistics_or_patterns`
- `coverage_limits`

何が存在するか、どのように分布しているか、どのcharacteristicが観測されるかを扱う。

description / associationからcausationを導かない。

## Comparative

Fields:

- `comparison_units`
- `comparison_dimensions`
- `contrasts`
- `comparability_limits`

定義されたunit間のsimilarity / differenceを扱う。

観測されたcontrastを自動的にcausal effectとみなさない。

## Causal

Fields:

- `exposure_or_treatment`
- `outcome`
- `estimand`
- `identification_strategy`
- `identification_assumptions`
- `threats_to_identification`

exposure / treatmentがoutcomeを変化させるか、どのように変化させるかを扱う。

causal conclusion自体は共通 `judgments` / Working Answerへ置き、profileはcausal identification structureを記録する。

associationのみをcausal effectとして表現しない。

## Mechanistic

Fields:

- `phenomenon`
- `components`
- `mechanism_steps`
- `intervention_or_perturbation_evidence`
- `alternative_mechanisms`
- `mechanistic_gaps`

phenomenonが生じるprocess / pathway / component / intermediate stepを扱う。

temporal sequenceやcorrelationだけでmechanismを確立しない。

## Predictive

Fields:

- `prediction_target`
- `prediction_horizon`
- `input_information`
- `evaluation_design`
- `performance_measures`
- `generalization_limits`

定義されたtargetのout-of-sample predictionを扱う。

predictive performanceからpredictorのcausal interpretationを導かない。

Evidenceが許す場合、training fitとheld-out / external performanceを区別する。

## Methodological

Fields:

- `method_or_procedure`
- `intended_use`
- `assumptions`
- `evaluation_criteria`
- `comparators`
- `tradeoffs`
- `applicability_limits`

method、procedure、measurement、algorithm、research designを扱う。

あるcriterionで優位でも別criterionでは劣りうるため、tradeoffをuniversal winnerへ潰さない。

## Conceptual

Fields:

- `concept`
- `proposed_definition`
- `dimensions`
- `boundary_cases`
- `relations_to_adjacent_concepts`
- `ambiguities`

definition、conceptual distinction、category、concept間relationを扱う。

conceptual coherenceをempirical confirmationとして扱わない。

## Schemaとの関係

canonical `schemas/v1/30_analysis.schema.json` は以下を持つ。

- common field
- required `question_type`
- required `profile`
- `question_type` で選択される8つのconditional profile schema

各profile内では `additionalProperties: false` を適用する。

例として、Causal profileへ `prediction_target` を入れることはinvalidである。

5つ目のartifactは追加しない。canonical chainは次を維持する。

`00_context -> 10_evidence -> 20_synthesis -> 30_analysis`

## Validation boundary

JSON Schemaが判定するのは、selected profileにfieldが属するか、構造typeが正しいかまでである。

以下はJSON Schemaの責務ではない。

- identification strategyが科学的に十分か
- predictive evaluationにleakageがないか
- proposed mechanismがEvidenceで支持されるか
- conceptual definitionが有用か

これらはsemantic Analysis / Reviewで判断する。
