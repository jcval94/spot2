# E006_architecture_rolling_cv

- Parent: E005_multihead_vs_specialists
- Primary change: replace the single temporal holdout evaluation with rolling-origin temporal cross-validation by lead cohort
- Leakage: PASS
- Comparison: NON_EQUIVALENT
  - population differs from parent
  - validation differs from parent

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.466513 |
| brier | 0.237198 |
| lift_top_10pct | 1.18667 |
| log_loss | 0.666906 |
| recall_top_20pct | 0.243458 |
| roc_auc | 0.572127 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | -0.0509625 |
| brier | -0.00800122 |
| lift_top_10pct | +0.070228 |
| log_loss | -0.0168449 |
| recall_top_20pct | +0.0234259 |
| roc_auc | +0.0160675 |

## Conclusion

SUPPORTED

## Caveats

- rolling CV changes the validation design relative to E005 and is therefore a robustness study rather than a direct parent delta
- scheduled_visit remains a proxy target
- the dataset is synthetic
- outer test cohorts are disjoint, but expanding training windows reuse older cohorts as later training data by design

## Next experiment

Add explicit point-in-time trajectory/progression features under the identical rolling CV folds and compare paired OOF deltas.
