# E022_temporal_feature_ablation

- Parent: E005_multihead_vs_specialists
- Primary change: remove calendar and funnel-progress timing features while holding model, target, population and frozen temporal split fixed
- Leakage: PASS
- Comparison: EQUIVALENT

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.484986 |
| brier | 0.24976 |
| lift_top_10pct | 1.00116 |
| log_loss | 0.692975 |
| recall_top_20pct | 0.202093 |
| roc_auc | 0.512168 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | -0.0324903 |
| brier | +0.00456097 |
| lift_top_10pct | -0.115286 |
| log_loss | +0.00922417 |
| recall_top_20pct | -0.0179383 |
| roc_auc | -0.0438911 |

## Conclusion

SUPPORTED

## Caveats

- The experiment removes calendar/progress clocks but retains availability snapshot age, which is audited separately in E023.
- The time-proxy-only model is diagnostic and includes lead_cohort_index and score_time_index; it is not proposed for production.
- Bootstrap resamples complete leads to preserve dependence among T2 snapshots.

## Next experiment

Audit availability snapshot age separately, because it is point-in-time safe but may behave as a regime/staleness proxy.
