# Question Type Analysis Profiles

## Purpose

`30_analysis` consists of common analysis fields plus a Question Type-specific `profile` selected by `question_type`. This prevents descriptive, causal, predictive, mechanistic, and other judgments from being represented with interchangeable semantics.

## Common fields

The following remain outside the profile and have the same meaning for every type:

- `working_answer`
- `judgments`
- `limitations`
- `unresolved_questions`
- `alternative_interpretations`
- lineage via `knowledge_unit_refs`

Profiles structure the analysis setup; they do not duplicate the final conclusion.

## Unknown / not applicable

Profile fields are optional unless a later method-specific contract makes them structurally mandatory. Unknown values are represented by omission, `null`, or an empty collection where allowed. Missing does not mean zero, false, no effect, or not applicable.

## Exploratory

Fields: `patterns`, `candidate_hypotheses`, `anomalies`, `evidence_gaps`.

Use for pattern discovery and hypothesis generation. Candidate hypotheses are not established causal conclusions.

## Descriptive

Fields: `target`, `constructs`, `summary_statistics_or_patterns`, `coverage_limits`.

Use for what exists, how something is distributed, or which characteristics are observed. Description and association do not imply causation.

## Comparative

Fields: `comparison_units`, `comparison_dimensions`, `contrasts`, `comparability_limits`.

Use for similarities and differences among defined units. An observed contrast is not automatically a causal effect.

## Causal

Fields: `exposure_or_treatment`, `outcome`, `estimand`, `identification_strategy`, `identification_assumptions`, `threats_to_identification`.

Use for whether/how an exposure or treatment changes an outcome. Causal conclusions remain in common judgments / Working Answer. Association alone is not a causal effect.

## Mechanistic

Fields: `phenomenon`, `components`, `mechanism_steps`, `intervention_or_perturbation_evidence`, `alternative_mechanisms`, `mechanistic_gaps`.

Use for pathways or processes through which a phenomenon occurs. Temporal sequence or correlation alone does not establish mechanism.

## Predictive

Fields: `prediction_target`, `prediction_horizon`, `input_information`, `evaluation_design`, `performance_measures`, `generalization_limits`.

Use for out-of-sample prediction. Predictive performance does not establish causal interpretation of predictors.

## Methodological

Fields: `method_or_procedure`, `intended_use`, `assumptions`, `evaluation_criteria`, `comparators`, `tradeoffs`, `applicability_limits`.

Use for methods, procedures, measurements, algorithms, or research designs. Tradeoffs are kept explicit rather than collapsed into a universal winner.

## Conceptual

Fields: `concept`, `proposed_definition`, `dimensions`, `boundary_cases`, `relations_to_adjacent_concepts`, `ambiguities`.

Use for definitions, distinctions, categories, or relations among concepts. Conceptual coherence is not empirical confirmation.

## Schema relationship

`schemas/v1/30_analysis.schema.json` contains the common fields, required `question_type`, required `profile`, and eight conditional profile schemas selected by `question_type`.

`additionalProperties: false` applies inside each profile. For example, `prediction_target` is invalid inside a Causal profile.

No fifth artifact is introduced; the canonical chain remains `00_context -> 10_evidence -> 20_synthesis -> 30_analysis`.

## Validation boundary

JSON Schema validates profile selection and structure. It does not decide whether causal identification is adequate, predictive evaluation is leakage-free, a mechanism is supported, or a concept is scientifically useful. Those are semantic analysis / review responsibilities.
