# E032 — T0 semantic recovery

**Status: NOT_RECOVERED**

Selected variant: **soft_profiles**

| Metric | Candidate | Atomic baseline |
|---|---:|---:|
| ROC-AUC | 0.4897 | 0.4892 |
| AP | 0.5016 | 0.5002 |
| AP / prevalence | 0.964x | 0.962x |
| Lift@10 | 0.824x | 0.797x |
| Recall@20 | 0.182 | 0.193 |
| Brier | 0.2570 | 0.2549 |

## Absolute uncertainty

- AUC 95% lead-bootstrap: **[0.4501, 0.5300]**.
- AP/prevalence 95%: **[0.911, 1.033]**.
- Lift@10 95%: **[0.621, 1.008]**.

## Delta vs atomic sanitized baseline

- Delta AUC: **+0.0005**, CI95% [-0.0362, +0.0353].
- Delta AP: **+0.0013**, CI95% [-0.0245, +0.0256].
- Delta Lift@10: **+0.027x**, CI95% [-0.162, +0.319].

## Recovery gate

RECOVERED requires simultaneously:

1. lower AUC CI95% > 0.50;
2. AP/prevalence >= 1.05;
3. Lift@10 >= 1.10;
4. candidate AP > atomic baseline AP.

PROMISING_NOT_CONFIRMED requires point AUC > 0.50, AP/prevalence >= 1.03 and Lift@10 >= 1.05.

No temporal clocks, Availability LeadQuality signal, broker outcome/prior or current-state Spot aggregates were introduced.
