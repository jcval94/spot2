# CALIBRATION — frozen T1 champion

Architecture selection finished on DEVELOPMENT before this step.

Frozen raw champion: constant DEVELOPMENT prevalence **0.2037546**.

Calibration population: **312** leads, prevalence **0.2083333**.

| Method | Brier | Log Loss | AP | Selected |
|---|---:|---:|---:|---|
| Raw | 0.164952 | 0.511804 | 0.20833 | No |
| Platt | **0.164932** | **0.511745** | 0.20754 | **Yes** |
| Isotonic | 0.164932 | 0.511745 | 0.20754 | No |

Isotonic was eligible by sample-size rule (N≥300 and ≥50 examples of each class), but it offered no material advantage over Platt. Under the pre-registered tie preference, **Platt** is retained.

The final Platt mapping was fit on all CALIBRATION rows:
- intercept: -0.46726765
- coefficient: 0.63688171
- calibrated constant probability: **0.20827878**

Because the raw model is constant, calibration only adjusts the probability level. It cannot create ranking discrimination.
