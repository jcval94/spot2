# Incremental plan

## P0 — Clean-room + temporal information contract — COMPLETE
Scoring instants and source observability frozen.

## P1 — Raw-data integrity and source semantics — COMPLETE
CSV/Parquet parity, PK/FK, missingness, temporal ontology and source-specific blocks.

## P2 — Target contract — COMPLETE
Primary target frozen as `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`, 14-day maturity.

## P3 / Prompt 4 — Point-in-time ABTs — COMPLETE FOR TEMPORAL VALIDITY
Builders and leakage gates are implemented. Independent raw-equivalence checks reproduce the frozen T0/T1/T2 and candidate grains.

Exact Polars/pytest execution remains a final reproducibility check when the project runtime is available; it is not a downstream selection dependency.

## P4 — Split contract — COMPLETE
Frozen timestamp-only T1 split plus four expanding temporal folds.

## P5–6 — EDA, drift and Feature Engineering — COMPLETE
Development-only FE design, drift classification, feature registry, stage-aware feature policies and Inventory separation are frozen.

## P7 — T1 Lead Quality initial model phase — SUPERSEDED BY RECOVERY
The earlier Base-Rate/no-ranking conclusion is historical only and must not be presented as the current champion.

Prompt 11.5 reopened **model signal recovery only**, without changing target or splits.

## P7R / Prompt 11.5 — Lead Quality recovery — COMPLETE
Current champion:

`LQ_RECOVERY_R4_STATIC_MATCH_V1`

Model:
- small regularized Logistic Regression;
- RAW calibration.

Features:
- `selected_spot_area_closeness`;
- `selected_spot_geographic_fit`;
- `selected_spot_attribute_completeness`.

Availability is not used in Lead Quality.

Recovery gate passed on temporal DEVELOPMENT OOF.

## P8 — T0 sensitivity + T2 challenger — COMPLETE / NON-CANONICAL FOR FINAL SCORER
T0/T2 work remains supporting/extension evidence. Final operational scoring authority is the frozen T1 post-recovery system.

## P9 / Prompt 11.6 — Inventory / Fallback / Opportunity Score rebuild — COMPLETE
Post-recovery dependencies were rebuilt.

Frozen state:
- Inventory scalar: `INV_SERVICEABILITY_V1_FROZEN_2026-08-30`;
- fallback: `K=3`;
- Opportunity Score: `OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`;
- formula: `lead_quality_probability * inventory_actionability_gate`;
- rejected V1 continuous product: diagnostic-only;
- capacity: `P80 / top 20% within T1`;
- selection population: DEVELOPMENT temporal OOF only;
- final red-team: PASS, 0 blockers.

Authority:

`recovery_downstream/POST_RECOVERY_FINAL_STATE.json`

## P10 / Prompt 12 — LLM / AI requirement — COMPLETE
Real LLM evidence is documented and the self-contained Rules-first implementation lives under `llm/**`.

Final role:
- sampled Semantic Inventory / Catalog QA discovery;
- no runtime dependency in Lead Quality or Opportunity Score.

Semantic Rules:
- excluded from Lead Quality scoring;
- retained for Inventory/Catalog QA.

Prompt 12 new API spend: USD 0.

## P11 / Prompt 13 — Final assessment packaging — NEXT
Build the final notebook, HTML, one-pager, presentation, Assessment Report and reproducibility index using only frozen AssessmentSol1 source-of-truth artifacts.

Authoritative patched prompt:

`final/PROMPT_13_FINAL_ASSESSMENT.md`

## P12 / Prompt 14 — Final submission review — AFTER PROMPT 13
Run the final stale-metric, post-recovery consistency, reproducibility and deliverable red-team.

Authoritative patched prompt:

`final/PROMPT_14_FINAL_REVIEW.md`

Final gate:
- `READY TO SUBMIT`, or
- `DO NOT SUBMIT — BLOCKERS REMAIN`.
