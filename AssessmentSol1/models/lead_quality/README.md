# Lead Quality T1 — historical Prompt 7 authority

> **SUPERSEDED FOR CURRENT T1 SCORING BY `../lead_quality_recovery/`.**

This directory preserves the original Prompt-7 Base-Rate decision, diagnostics, calibration artifacts and the June holdout incident chronology. Those artifacts remain useful evidence for why recovery was needed, but they are **not the current production/scoring authority**.

Current Lead Quality authority:
- `../lead_quality_recovery/RECOVERY_DECISION.md`
- `../lead_quality_recovery/frozen_recovered_model_config.json`
- `../lead_quality_recovery/predictions/development_oof.csv`
- `../lead_quality_recovery/predictions/full_scoring_predictions.csv`

Current champion: `LQ_RECOVERY_R4_STATIC_MATCH_V1`, RAW calibration.

The original `BASE_RATE + RAW` configuration under this directory must not be reused for current Opportunity Score construction.

June remains `DIAGNOSTIC_ONLY_NON_PRISTINE` and cannot change post-recovery decisions.
