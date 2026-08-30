# Models — current status

T1 Lead Quality modeling is complete and frozen.

Champion: **BASE_RATE + RAW**.

This is an evidence-backed neutral prior, not a ranking engine. Learned Logistic/CatBoost challengers did not demonstrate defensible superiority under temporal CV.

Key files:
- `lead_quality/MODEL_SELECTION.md`
- `lead_quality/MODEL_CARD.md`
- `lead_quality/THRESHOLD_POLICY.md`
- `lead_quality/CALIBRATION.md`
- `lead_quality/FROZEN_MODEL_CONFIG.json`
- `lead_quality/HOLDOUT_INCIDENT.md`

T0/T2 remain future stage analyses and must not modify the frozen T1 decision.
