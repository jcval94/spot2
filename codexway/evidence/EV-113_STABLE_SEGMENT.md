# EV-113 — stable segment Lead Quality

- Experiment: `experiments/specs/E113_stable_segment_logistic.json`
- Immutable record: `experiments/records/E113.json`
- Interpretation correction: `experiments/specs/E115_retrospective_evidence_correction.json`
- Status: **SUPPORTED**, retrospective / procedural holdout
- Primary change: replace the broad feature set with
  `Industrial AND (company_size=small OR source=paid)`.
- Leakage: **PASS**. All three inputs are present on the lead row at creation;
  no target, response, future inquiry, mutable counter or snapshot is used.

## Evidence

- Rolling train mean Lift@10: 1.186x; three of four folds above 1.
- Frozen validation Lift@10: 1.449x.
- Procedural holdout Lift@10: 1.672x; bootstrap 95% CI 1.381–1.984.
- Holdout PR-AUC: 0.2391 versus prevalence 0.2122.
- Holdout Brier after validation calibration: 0.1658 versus constant 0.1672.

## Caveat and next step

The historical holdout was globally inspected by earlier research, and the
interaction hypothesis was formulated within that already-consumed research
environment, so this is not a pristine confirmation set. The executable promotion
gate itself reads only rolling train folds and validation. Run a new forward
shadow cohort before changing operations. Source metrics: `outputs/metrics/t1_model_metrics.json`,
`outputs/metrics/t1_metric_intervals.csv` and
`outputs/metrics/rolling_model_comparison.csv`.
