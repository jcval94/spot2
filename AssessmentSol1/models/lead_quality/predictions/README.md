# Predictions

Prediction populations are physically separate and labeled:

- `champion_development_oof.csv` — DEVELOPMENT OOF;
- `calibration_predictions.csv` — CALIBRATION;
- `procedural_holdout_predictions.csv` — June **DIAGNOSTIC_ONLY_NON_PRISTINE**.

The frozen champion is `BASE_RATE + RAW`; all final T1 probabilities are constant at the appropriate frozen base-rate value. Never concatenate populations without retaining the population label.
