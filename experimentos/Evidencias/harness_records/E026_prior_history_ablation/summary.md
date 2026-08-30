# E026_prior_history_ablation

- Parent: E005_multihead_vs_specialists
- Primary change: ablate prior_searches and prior_inquiries separately and jointly under the frozen RF benchmark
- Leakage: PASS
- Comparison: EQUIVALENT

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.523871 |
| brier | 0.244724 |
| lift_top_10pct | 1.11955 |
| log_loss | 0.682653 |
| recall_top_20pct | 0.230507 |
| roc_auc | 0.562655 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | +0.0063947 |
| brier | -0.000475333 |
| lift_top_10pct | +0.00309897 |
| log_loss | -0.00109801 |
| recall_top_20pct | +0.0104755 |
| roc_auc | +0.00659516 |

## Conclusion

NOT_SUPPORTED

## Caveats

- Near-zero raw correlation does not imply redundancy; this experiment uses predictive ablation to test incremental contribution.
- Both fields are fixed lead-intake information and point-in-time safe at T0/T1/T2.

## Next experiment

Add a strictly point-in-time smoothed broker history prior without using broker identity itself.
