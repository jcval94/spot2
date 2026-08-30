# CALIBRATION — T1 frozen champion

Architecture/model selection was completed on DEVELOPMENT before calibration.

Frozen raw champion: constant DEVELOPMENT prevalence **0.2037546**.

CALIBRATION population: **312** leads; prevalence **0.2083333**.

| Method | Brier | Log Loss | Increment vs raw | Selected |
|---|---:|---:|---:|---|
| Raw | 0.164952 | 0.511804 | — | **Yes** |
| Platt | 0.164932 | 0.511745 | ~0.00002 / 0.00006 | No |
| Isotonic | 0.164932 | 0.511745 | ~0.00002 / 0.00006 | No |

The pre-registered rule says that RAW wins when learned calibration does not improve proper scoring **materially**. The existing 0.001 practical-tie tolerance is used as the materiality floor. Neither learned calibrator reaches it.

Therefore final calibrator: **RAW**.

Final probability for every T1 row: **0.2037545788**.

Because the champion is constant, calibration cannot create ranking discrimination. See `CALIBRATION_RULE_CORRECTION.md` for the documented post-holdout methodological correction.
