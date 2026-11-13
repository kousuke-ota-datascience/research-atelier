# INV-000041 — Search and coverage audit (supporting record)

## Research objective
Map documented applications of time-series anomaly detection, change-point detection, fault diagnosis, future-event prediction, and remaining useful life (RUL) to industry/business use cases and downstream decisions under frozen RQ-000040. This is a **structured, purposive scoping search**, not a formally exhaustive PRISMA-compliant systematic review.

## Date and boundaries
- Search conducted: 2026-11-13 (Asia/Tokyo).
- Search engines / repositories: web-index searches with targeted publisher / institutional landing pages (Nature/Scientific Data, Springer, IEEE, ACM KDD, NIST, USGS, USENIX/Google Research, PHM Society, DCASE, PhysioNet, NREL, J-STAGE, OnePetro, manufacturer/operator primary pages).
- Time period: not limited by year. New accessible sources through 2026-11-13 considered; no retrospectively invented evidence cutoff.
- Starting collection: 10 sources in INV-000040, including earlier warnings about wind gearbox event-log-only evidence.
- Search expansion: 25 additional primary papers / official datasets / direct institutional/operator pages (SRC-000229–SRC-000253). Reuse source identity rather than duplicating RQ-scoped entries.
- The numerical range of 30–50 sources is only a workload guide; no claim of saturation or population coverage is made.

## Recorded targeted queries (substantive patterns)
- predictive maintenance wind turbine SCADA real field bearing stoppage prediction
- MetroPT train air compressor actual failure prediction lead time
- early prediction of sepsis 2019 PhysioNet 6 hours
- battery early cycle life estimation original 2019
- Google production hard disk failure SMART prediction limitations
- power grid field PMU event detection / change-point and load estimation
- real-world automotive body-in-white manufacturing online change point
- semiconductor manufacturing failure timing pre-shipment / wafer handling robot prognosis
- telecom operator KPI SARIMA anomalies / 5G network KPI monitoring
- oil-well production anomaly sensor data 3W / ESP life / oil valve incidents
- pressure transient field pipeline water leak location
- financial transaction AML production unsupervised anomaly
- aircraft airline operator prognostic alerts / Boeing aircraft maintenance
- USGS ShakeAlert earthquake warning
- industrial reverse osmosis plant sensor prediction and maintenance integration
- railway turnout field sensing failure mode experiments

## Selection / exclusion criteria
Include original studies, official datasets and operational documentation that state at least a domain, use case, measurable time-series/temporal input, and analytical target. Source's own evidence may be a benchmark, a field evaluation, an operator-reported implementation, or observational real-life data; annotate which. Include relevant negative evidence (e.g., difficulty of individual drive failure prediction) to prevent selection bias.

Do not treat an alarm score as calibrated failure probability; do not treat historical failure-log frequency or generic asset taxonomy as an implemented time-series detector; do not conflate prospective clinical alerts with retrospective challenge testing; do not generalize before-after site comparisons causally. An implementation claim from vendor pages is labeled vendor-reported.

## Provisional extraction matrix columns
source_id; industry; asset/system; business use case; decision/action; input series and sampling; analytical target/event; current-vs-future horizon; output (score/class/event/risk/time); source's evaluation level; caveat; evidence_id.

## Coverage checkpoints
- Methods explicitly sought: current anomaly detection, change-point/event detection, fault classification/diagnostics, future failure/alarm risk, RUL/cycle life.
- Sectors sampled: manufacturing, electronics/semiconductors, rail, aviation, wind, electric grid, datacenter/storage, telecom, oil & gas, water infrastructure, finance, healthcare, batteries, natural hazards, and buildings.
- Evidence level is tracked separately from industry and analytical target; blank/undemonstrated cells remain open gaps rather than being filled by inference.
- Coverage is not completeness. An additional citation-chaining and independent full-text screening pass would be required for comprehensive scoping-review claims.
