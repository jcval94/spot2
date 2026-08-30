# E027_broker_prior_point_in_time

- Parent: E005_multihead_vs_specialists
- Primary change: add historical broker response/support and smoothed scheduled-visit prior features constructed strictly before each scoring time
- Leakage: PASS
- Comparison: EQUIVALENT

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.519012 |
| brier | 0.245537 |
| lift_top_10pct | 1.07881 |
| log_loss | 0.684413 |
| recall_top_20pct | 0.227451 |
| roc_auc | 0.557821 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | +0.00153623 |
| brier | +0.00033781 |
| lift_top_10pct | -0.0376344 |
| log_loss | +0.000661653 |
| recall_top_20pct | +0.00741945 |
| roc_auc | +0.00176124 |

## Conclusion

INCONCLUSIVE

## Caveats

- Broker history uses only response_event_at strictly before score_time; the current inquiry response can never enter its own features.
- Laplace smoothing is fixed Beta(1,1) and does not use future/full-dataset target prevalence.
- This is predictive association, not a causal broker-quality estimate.
- T0 has no current spot/broker assignment, so broker-history features are missing there by design.

## Next experiment

If broker prior is promising, validate it on a later cohort and test routing causally; otherwise retain broker only as an analysis dimension.
