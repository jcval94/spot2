# Incremental plan

## P0 — Clean-room + temporal information contract — COMPLETE

- inventory prior evidence;
- record conflicts and research contamination;
- define exact scoring instants;
- classify sources as observable / conditional / audit-only / blocked.

Gate: answer “What information is known at the exact scoring instant?” for T0, T1, T2, inventory, broker response and market context.

## P1 — Raw-data integrity and source semantics — COMPLETE

Re-profiled all six raw tables from scratch; validated CSV↔Parquet parity, physical fingerprints, keys, cardinalities, timestamp ordering, missingness, duplicates, outliers, modality structure, response inconsistencies, Availability as-of coverage and source temporal provenance. Parquet is canonical. No target was constructed.

Gate: every raw column has explicit event/observation/effective-time semantics or is blocked/EDA-only.

## P2 — Target contract — COMPLETE

Compared Target A (first-inquiry eventual scheduled_visit), Target B (E028-style 30d reconstructed response event), and Target C (30d inquiry-initiation progress) without training a model or using AUC/AP/Lift. Frozen the primary T1 target as `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` with a 14-day historical maturity buffer. T0 has a separate secondary progress estimand; T2 outcome semantics are frozen but its point-in-time cohort gate is deferred to the ABT phase.

Gate: target estimand and maturity are frozen before FE/modeling and may not be changed because another target later gives better model performance.

## P3 — Splits and research-contamination-aware evaluation

Create development splits before FE/model fitting. Historical candidate periods are development/research-contaminated unless a protocol was frozen before their inspection. Reserve only a procedural final holdout if useful; true confirmation is new data/hidden evaluator.

## P4 — Canonical ABTs

Build T0/T1/T2 from raw tables under the frozen point-in-time contract. Produce an audit table and model-ready views. No historical ABT may be imported.

## P5 — Feature engineering

Start with deterministic, explainable features. Fit any learned transform inside training folds only. Every feature gets provenance, availability time, mutation risk and leakage tests.

## P6 — Lead Quality models

Benchmark simple baselines before complex models. Use temporal/lead-grouped validation and calibration. T0/T1 neutrality from prior research is a prior belief, not a forced result.

## P7 — Inventory serviceability + fallback

Build inventory logic independently from Lead Quality, using only point-in-time inventory. Separate catalog-quality QA from propensity modeling.

## P8 — Opportunity Score

Combine validated Lead Quality and Inventory Serviceability only after each component has its own contract and evidence.

## P9 — LLM

Use an LLM only where unstructured information exists and where deterministic extraction is not an equivalent cheaper solution. Historical E017/E018 are negative evidence for current structured/listing-copy LeadQuality features.

## P10 — Final reporting

Produce notebook, one-pager, slides, figures, audit and reproducibility manifest. Do not relabel a research-contaminated period as unseen.
