# Lead Quality T1 modeling

T1 is the principal predictive product.

The modeling pipeline is deliberately narrow:

1. Base-rate baseline.
2. Fixed interpretable business rule.
3. L2 Logistic Regression.
4. CatBoost as the only primary nonlinear challenger.

Feature families and ablations are frozen in `../../features/ablation_plan.json`. Promotion is frozen in `MODEL_PROMOTION_RULE.json`.

No script may evaluate `PROCEDURAL_HOLDOUT` unless `FROZEN_MODEL_CONFIG.json` already exists with `status = FROZEN`. Development and calibration outputs are physically separated from procedural-holdout predictions.

The code is designed to rebuild P4 ABTs/features from raw data before fitting; it never consumes historical `experimentos/**` matrices, predictions, models or preprocessors.
