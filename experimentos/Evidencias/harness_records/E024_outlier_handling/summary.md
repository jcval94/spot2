# E024_outlier_handling

- Parent: E005_multihead_vs_specialists
- Primary change: remove training-only Isolation Forest anomalies while keeping validation and test populations untouched
- Leakage: PASS
- Comparison: EQUIVALENT

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.523739 |
| brier | 0.245045 |
| lift_top_10pct | 1.09774 |
| log_loss | 0.683355 |
| recall_top_20pct | 0.224656 |
| roc_auc | 0.55939 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | +0.00626316 |
| brier | -0.000153761 |
| lift_top_10pct | -0.0187031 |
| log_loss | -0.000396223 |
| recall_top_20pct | +0.00462406 |
| roc_auc | +0.00333039 |

## Conclusion

INCONCLUSIVE

## Caveats

- Isolation Forest is fit only on training data, outcome-free, with stage/sector/modality regimes and stage fallback.
- Temporal clocks and availability snapshot age are intentionally excluded from anomaly detection so anomaly does not simply mean late cohort.
- Held-out validation and test rows are never deleted.

## Next experiment

Remove deterministic Spot price-total redundancy while keeping the held-out population fixed.
