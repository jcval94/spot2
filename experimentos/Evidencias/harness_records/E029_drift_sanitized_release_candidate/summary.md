# E029_drift_sanitized_release_candidate

- Parent: E005_multihead_vs_specialists
- Primary change: Build and freeze a T2-only LeadQuality candidate with corrected ambiguous-event target semantics and a sanitized feature policy; T0/T1 remain neutral.
- Leakage: PASS
- Comparison: NON_EQUIVALENT
  - scoring_time differs from parent
  - target differs from parent
  - population differs from parent
  - validation differs from parent

## Metrics

| Metric | Value |
|---|---:|
| average_precision | 0.542392 |
| brier | 0.24927 |
| lift_top_10pct | 1.14696 |
| log_loss | 0.69173 |
| recall_top_20pct | 0.221893 |
| roc_auc | 0.542845 |

## Delta vs parent

| Metric | Delta |
|---|---:|
| average_precision | +0.0249156 |
| brier | +0.00407117 |
| lift_top_10pct | +0.0305108 |
| log_loss | +0.00797871 |
| recall_top_20pct | +0.00186182 |
| roc_auc | -0.0132141 |

## Conclusion

INCONCLUSIVE

## Caveats

- Historical diagnostics are post-selection because E021-E027 already used this dataset to choose the feature policy.
- Canonical ambiguous event-time labels are excluded rather than coerced to zero.
- T0/T1 are deliberately neutral; this artifact is T2-only.
- No Availability fields or drift-sensitive clocks enter LeadQuality.
- Launch requires a genuinely post-freeze cohort and production A/A instrumentation.

## Next experiment

Apply prospective_gate.json to the first post-freeze matured cohort; if PASS, complete E028 release manifest and productive A/A.
