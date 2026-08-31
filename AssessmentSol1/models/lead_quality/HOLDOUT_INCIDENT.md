# HOLDOUT_INCIDENT — procedural holdout integrity

**Status:** `CONSUMED_BY_METHOD_INCIDENT_BEFORE_FREEZE`

## What happened

During the execution bridge used to move the frozen T1 table into the local runtime, the temporary binary export encoded the target field for rows belonging to `PROCEDURAL_HOLDOUT` **before** `FROZEN_MODEL_CONFIG.json` existed.

No procedural-holdout metric was calculated, no individual holdout label was inspected for decision-making, and model/feature/calibration selection physically filtered to DEVELOPMENT or CALIBRATION. Nevertheless, the prompt explicitly requires the holdout not to be touched before freeze. Encoding those labels violates that stricter requirement.

## Consequence

The holdout is treated as **consumed**. It is not described as pristine or unseen anywhere in AssessmentSol1.

The frozen champion is selected solely from:
- DEVELOPMENT for baselines, ablations and architecture;
- CALIBRATION for calibrator selection.

Any later score reported on the June holdout is **diagnostic-only, non-pristine**, and cannot trigger model, feature, hyperparameter or calibrator changes.

## Containment

- Target, maturity, split boundaries, feature registry and ablation plan were not changed.
- No holdout row entered DEVELOPMENT folds.
- No holdout row entered CALIBRATION.
- The incident does not authorize another holdout.
- True confirmatory performance requires new/hidden future data.

This incident is methodological, not a performance-driven exception.
