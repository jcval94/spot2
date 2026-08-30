# SPLIT_CONTRACT — frozen before Feature Engineering

**Version:** `SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30`

The split is anchored on the deterministic **T1 first-inquiry `score_time`** and was frozen using timestamps only. Target labels and model performance were not inspected to choose these boundaries.

## Primary partitions

| Partition | T1 score_time | Leads | Use |
|---|---|---:|---|
| DEVELOPMENT | < 2026-05-01 UTC | 4368 | EDA, drift, FE design, rolling model selection |
| CALIBRATION | 2026-05-01 to < 2026-06-01 | 312 | calibrator fit/selection only after architecture freeze |
| PROCEDURAL_HOLDOUT | 2026-06-01 to < 2026-07-01 | 290 | sealed until FROZEN_MODEL_CONFIG.json exists |
| POST_HOLDOUT_AUDIT | >= 2026-07-01 | 30 | partial/maturity audit only; never model selection |

## Development folds

| Fold | Train | Validation | Train N | Validation N |
|---|---|---|---:|---:|
| F1 | score_time < 2025-09-01 | 2025-09-01 to < 2025-11-01 | 1978 | 607 |
| F2 | score_time < 2025-11-01 | 2025-11-01 to < 2026-01-01 | 2585 | 602 |
| F3 | score_time < 2026-01-01 | 2026-01-01 to < 2026-03-01 | 3187 | 578 |
| F4 | score_time < 2026-03-01 | 2026-03-01 to < 2026-05-01 | 3765 | 603 |

All folds are expanding-window and lead-isolated.

## Hard rules

- Learned preprocessing fits on each fold's TRAIN rows only.
- Validation never participates in imputation, category filtering, encoding, clustering, scaling, or model fitting.
- CALIBRATION is not used for feature/model selection.
- PROCEDURAL_HOLDOUT is not opened during EDA, drift, FE, ablations, architecture selection, hyperparameter decisions, or calibration selection.
- July-2026 is a partial-period/post-holdout audit slice, not a tuning set.
- For T2, lead membership alone is insufficient: a train-cohort lead's later T2 rows are truncated at each fold validation boundary.
- Split boundaries are immutable unless a leakage/implementation bug is documented and the affected holdout is treated as consumed.

The machine-readable authority is `split_contract.json`. `split_assignments_t1.csv` contains timestamp-only assignments and no target column.
