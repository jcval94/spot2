# Incremental plan

## P0 — Clean-room + temporal information contract — COMPLETE
Scoring instants and source observability frozen.

## P1 — Raw-data integrity and source semantics — COMPLETE
CSV/Parquet parity, PK/FK, missingness, temporal ontology and source-specific blocks.

## P2 — Target contract — COMPLETE
Primary target frozen as `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`, 14-day maturity.

## P3 / Prompt 4 — Point-in-time ABTs — COMPLETE FOR TEMPORAL VALIDITY
Builders and leakage gates are implemented. An independent raw-equivalence runtime audit now passes and reproduces the frozen T0/T1/T2 and candidate grains.

Exact Polars builder materialization remains a final reproducibility follow-up, not a downstream selection dependency.

## P4 — Split contract — COMPLETE
Frozen timestamp-only T1 split plus four expanding folds; T2 boundary-crossing rule is active.

## P5–6 — EDA, drift and Feature Engineering — COMPLETE
Development-only FE design, drift classification, 129-row feature registry, stage-aware trajectory implementation and Inventory separation.

## P7 — T1 Lead Quality — COMPLETE
Champion: **BASE_RATE + RAW**, p≈0.2038. No ranking model is supported.

Permanent caveat: procedural holdout consumed by the documented execution-export incident; June is diagnostic-only.

## P8 — T0 sensitivity + T2 challenger — COMPLETE

### T0
**NEUTRAL_EVIDENCE_BACKED.**
Strong exposure drift is reproduced. Intake Logistic fails the frozen promotion rule.

### T2
**FUTURE_EXTENSION.**
Trajectory adds only +0.005 AP macro and does not justify operational complexity.

Boundary crossing audit confirms that 1,281–1,745 late T2 rows per fold would leak if lead membership alone were used; current-score-time truncation excludes them.

## P9 — Inventory / Fallback / Opportunity Score — NEXT
This is now the highest-value remaining assessment work.

Required focus:
1. define Inventory Serviceability under current temporal limits;
2. distinguish UNKNOWN, stale, unavailable and available;
3. implement fallback by sector/modality/geography/area;
4. treat historical price compatibility conservatively because prices are unversioned;
5. combine the frozen T1 prior with Inventory through a clearly justified Lead Opportunity Score;
6. evaluate end-to-end prioritization without pretending T1 has individual ranking signal.

## P10 — Final reporting
Produce the final HTML/notebook narrative, executive one-pager, presentation, AI-use disclosure, scalability/product vision and reproducibility index.
