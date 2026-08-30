# E025_redundancy_ablation

- Parent: E005_multihead_vs_specialists
- Primary change: remove deterministic raw Spot total-price columns while holding match ratios and all other features fixed
- Leakage: PASS
- Comparison: EQUIVALENT

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.519794 |
| brier | 0.245059 |
| lift_top_10pct | 1.07289 |
| log_loss | 0.683433 |
| recall_top_20pct | 0.22315 |
| roc_auc | 0.553289 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | +0.00231849 |
| brier | -0.000140328 |
| lift_top_10pct | -0.043554 |
| log_loss | -0.000318336 |
| recall_top_20pct | +0.00311878 |
| roc_auc | -0.00277027 |

## Conclusion

INCONCLUSIVE

## Caveats

- Non-inferiority margin is -0.01 for macro AP and macro ROC-AUC.
- Lead-Spot budget ratios are retained; the experiment tests direct redundancy of raw Spot total-price columns, not the value of economic fit.

## Next experiment

Ablate prior_searches and prior_inquiries separately to test whether their near-zero correlation corresponds to distinct predictive signal.
