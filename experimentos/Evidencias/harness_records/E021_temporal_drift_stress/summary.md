# E021_temporal_drift_stress

- Parent: E005_multihead_vs_specialists
- Primary change: replace the single 70/15/15 evaluation with expanding rolling temporal folds while holding target, point-in-time features and model family fixed
- Leakage: PASS
- Comparison: NON_EQUIVALENT
  - validation differs from parent

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.474711 |
| brier | 0.236853 |
| lift_top_10pct | 1.22632 |
| log_loss | 0.666269 |
| recall_top_20pct | 0.244277 |
| roc_auc | 0.576762 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | -0.0427653 |
| brier | -0.0083458 |
| lift_top_10pct | +0.109875 |
| log_loss | -0.017482 |
| recall_top_20pct | +0.0242454 |
| roc_auc | +0.0207026 |

## Conclusion

SUPPORTED

## Caveats

- Rolling folds deliberately change the validation design relative to E005, so comparison is NON_EQUIVALENT.
- Average Precision is prevalence-sensitive; AP/prevalence and ROC-AUC are reported alongside AP.
- The dataset is synthetic and the target is scheduled_visit within 30 days.

## Next experiment

Remove drift-sensitive timing/progress variables under the original frozen E005 split and quantify the performance delta.
