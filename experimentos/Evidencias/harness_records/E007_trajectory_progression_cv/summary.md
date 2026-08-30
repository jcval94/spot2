# E007_trajectory_progression_cv

- Parent: E006_architecture_rolling_cv
- Primary change: add explicit point-in-time trajectory/progression and stalling features
- Leakage: PASS
- Comparison: EQUIVALENT

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.476426 |
| brier | 0.23445 |
| lift_top_10pct | 1.21001 |
| log_loss | 0.66077 |
| recall_top_20pct | 0.244602 |
| roc_auc | 0.584927 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | +0.00991285 |
| brier | -0.00274741 |
| lift_top_10pct | +0.023339 |
| log_loss | -0.00613643 |
| recall_top_20pct | +0.00114416 |
| roc_auc | +0.0127996 |

## Conclusion

SUPPORTED

## Caveats

- trajectory features are evaluated by rolling temporal OOF predictions rather than a single holdout
- scheduled_visit remains a proxy target
- the dataset is synthetic
- the exploratory trajectory hybrid is selected repeatedly on fold validation sets and should not be treated as a production winner without further temporal confirmation

## Next experiment

If trajectory features are supported, ablate the winning trajectory family and audit temporal stability of the strongest individual progression signals.
