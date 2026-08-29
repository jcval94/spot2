# E005_multihead_vs_specialists

- Parent: E003_modelo_3_multihead
- Primary change: replace the modeling family while holding scoring time, target, population, features and temporal validation fixed
- Leakage: PASS
- Comparison: EQUIVALENT

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.517476 |
| brier | 0.245199 |
| lift_top_10pct | 1.11645 |
| log_loss | 0.683751 |
| recall_top_20pct | 0.220032 |
| roc_auc | 0.556059 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | +0.00916349 |
| brier | -0.00370289 |
| lift_top_10pct | -0.00137474 |
| log_loss | -0.00743031 |
| recall_top_20pct | -0.000507663 |
| roc_auc | +0.0230613 |

## Conclusion

INCONCLUSIVE

## Caveats

- scheduled_visit is a supervised proxy rather than the hidden final commercial outcome
- the dataset is synthetic
- the validation-selected hybrid evaluates a model-selection strategy and may carry validation selection bias
- multiple challenger families are tested, so small point differences are not treated as decisive without lead-level bootstrap support

## Next experiment

Engineer explicit trajectory/progression and stalling features on the best stage architecture, then compare against this frozen benchmark.
