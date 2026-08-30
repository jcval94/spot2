# E033 — T1 semantic recovery

**Status: NOT_RECOVERED**

Selected variant: **semantic_interactions**

| Metric | Candidate | Atomic baseline |
|---|---:|---:|
| ROC-AUC | 0.4637 | 0.4975 |
| AP | 0.5095 | 0.5245 |
| AP / prevalence | 0.962x | 0.990x |
| Lift@10 | 0.833x | 0.944x |
| Recall@20 | 0.160 | 0.185 |
| Brier | 0.2582 | 0.2543 |

## Absolute uncertainty

- AUC 95% lead-bootstrap: **[0.4213, 0.5031]**.
- AP/prevalence 95%: **[0.907, 1.030]**.
- Lift@10 95%: **[0.648, 1.092]**.

## Delta vs atomic sanitized baseline

- Delta AUC: **-0.0338**, CI95% [-0.0664, -0.0022].
- Delta AP: **-0.0150**, CI95% [-0.0447, +0.0099].
- Delta Lift@10: **-0.111x**, CI95% [-0.328, +0.108].

## Recovery gate

RECOVERED requires simultaneously:

1. lower AUC CI95% > 0.50;
2. AP/prevalence >= 1.05;
3. Lift@10 >= 1.10;
4. candidate AP > atomic baseline AP.

PROMISING_NOT_CONFIRMED requires point AUC > 0.50, AP/prevalence >= 1.03 and Lift@10 >= 1.05.

No temporal clocks, Availability LeadQuality signal, broker outcome/prior or current-state Spot aggregates were introduced.
