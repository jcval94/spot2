# EV-114 — Opportunity absolute lift gate

- Experiment: `experiments/specs/E114_opportunity_with_stable_quality.json`
- Immutable record: `experiments/records/E114.json`
- Status: **SUPPORTED for absolute Lift; NOT_SUPPORTED for incremental inventory value**.

## Evidence

- Conservative Opportunity Lift@10: 1.370x.
- Bootstrap 95% CI: 1.078–1.690.
- PR-AUC: 0.2477 versus prevalence 0.2122.
- Availability future-snapshot violations: zero.
- Inventory reduces Lift relative to E113 Lead Quality (1.672x); its incremental
  gate is therefore NO-GO.

## Interpretation

The score clears the user's absolute top-decile objective and may enter new
forward validation. It does not prove fallback causal value because the observed
T1 target is first-inquiry scheduling, not acceptance of a recommended alternative.
Source: `outputs/metrics/system_evaluation.json` and `system_score_*` tables.
