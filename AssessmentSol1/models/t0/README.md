# T0 Cold Start

Status: **NEUTRAL_EVIDENCE_BACKED**.

The only allowed predictor information is intake state at `lead.created_at`.

Macro temporal CV:
- Base Rate AP: **0.4803**
- Intake Logistic AP: **0.4856**
- Intake Logistic AUC: **0.4947**
- Brier worsens slightly: 0.2631 → 0.2642

No discriminative T0 model is promoted.

The strong temporal target drift is explained primarily by future inquiry exposure. That exposure is audit-only and cannot be used as a T0 predictor.

See:
- `../../evidence/T0_EXPOSURE_DRIFT.md`
- `metrics/fold_metrics.csv`
- `metrics/exposure_drift.csv`
- `train.py`
