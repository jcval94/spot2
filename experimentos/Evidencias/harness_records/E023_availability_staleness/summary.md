# E023_availability_staleness

- Parent: E005_multihead_vs_specialists
- Primary change: replace raw availability_snapshot_age_days with a staleness-aware guarded representation
- Leakage: PASS
- Comparison: EQUIVALENT

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.517259 |
| brier | 0.245278 |
| lift_top_10pct | 1.05135 |
| log_loss | 0.683868 |
| recall_top_20pct | 0.220032 |
| roc_auc | 0.551787 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | -0.000217394 |
| brier | +7.94846e-05 |
| lift_top_10pct | -0.0650968 |
| log_loss | +0.000117279 |
| recall_top_20pct | +0 |
| roc_auc | -0.0042721 |

## Conclusion

SUPPORTED

## Caveats

- Non-inferiority margin for macro AP was declared as -0.01 before reading the result.
- A stale snapshot is not equivalent to an unavailable spot; >90d is treated as unknown context, not false availability.
- Snapshot age is point-in-time safe but can still proxy temporal regime.

## Next experiment

Test training-row anomaly handling without contaminating the held-out test population.
