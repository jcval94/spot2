# Incremental plan

## P0 — Clean-room + temporal information contract — COMPLETE
Frozen scoring instants and source observability policy.

## P1 — Raw-data integrity and source semantics — COMPLETE
CSV↔Parquet parity, PK/FK, missingness, temporal ontology and source-specific blocks.

## P2 — Target contract — COMPLETE
Frozen primary target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`, 14-day maturity.

## P3 / Prompt 4 — Point-in-time ABTs — IMPLEMENTED; POLARS RUNTIME MANIFEST PENDING
T0, T1, T2 and separate Inventory/Matching builders are implemented with lineage/leakage gates. The full `validate_abts.py` materialization still needs an environment with Polars before final packaging.

## P4 — Split contract — COMPLETE
Frozen timestamp-only split:
- DEVELOPMENT 4,368;
- CALIBRATION 312;
- PROCEDURAL_HOLDOUT 290;
- POST_HOLDOUT_AUDIT 30;
plus 4 expanding temporal folds.

## P5–6 — EDA, drift and stage-aware Feature Engineering — COMPLETE
Development-only EDA, drift classification, 129-row FEATURE_REGISTRY, frozen feature groups/ablations, fold-aware transforms, T2 strict-prior trajectory implementation.

## P7 — Lead Quality T1 — COMPLETE WITH HOLDOUT-INTEGRITY INCIDENT

Frozen champion: **BASE_RATE + RAW**.

Why:
- learned T1 ranking is not stable;
- Logistic A AP advantage over Base Rate is not statistically decisive;
- Logistic A worsens Brier;
- CatBoost fails frozen promotion;
- selected-Spot context remains challenger-only;
- no post-result feature/model search was opened.

The champion outputs the DEVELOPMENT base rate ~0.2038 and must not be presented as an individual ranking model. Learned calibration was rejected after a methodological audit because its gain was immaterial.

The June procedural holdout is considered consumed because of the documented pre-freeze execution-export incident. Its stored results are diagnostic-only.

## PRE-P8 AUDIT — COMPLETE; ONE BLOCKER OPEN

Assessment alignment, drift, feature registry, metric semantics, Inventory timing assumptions and P7 calibration were audited. See `evidence/PRE_P8_AUDIT.md`.

**Blocker:** authoritative Prompt-4 runtime artifacts are still absent. Run `python AssessmentSol1/abt/validate_abts.py` and require `p4_qa_summary.json = PASS` before continuing.

## P8 — T0 sensitivity + T2 trajectory challenger — BLOCKED ON P4 RUNTIME PASS
T1 must remain frozen. Evaluate T0 as a potentially neutral cold-start product and T2 only as BASELINE vs TRAJECTORY under strict boundary crossing rules.

## P9 — Inventory / opportunity integration
Keep Lead Quality and Inventory independent; use explicit ablations/integration contracts.

## P10 — Final reporting
Before final packaging:
1. execute the pending P4 Polars runtime gate;
2. carry the P7 holdout caveat visibly;
3. produce HTML presentation / final evidence index;
4. do not relabel June as unseen;
5. reserve new/hidden data for true confirmation.
