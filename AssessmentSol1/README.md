# AssessmentSol1 — clean-room definitive assessment

Status: **PRE-P8 AUDIT COMPLETE; P8 BLOCKED ONLY ON THE PROMPT-4 RUNTIME PASS.**

This directory is the only writable home for the definitive Spot2 assessment. Historical experiments may be read as prior evidence but are not runtime dependencies.

## Frozen foundations

- raw/source audit: complete;
- temporal semantics: frozen;
- target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`;
- maturity: 14 days;
- split contract: `SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30`;
- point-in-time ABT architecture: implemented;
- feature registry / ablation plan: frozen;
- Lead Quality T1 champion: **BASE_RATE + RAW**.

## P7 result

Development contained 4,368 leads and Calibration 312.

No learned model demonstrated defendible superiority to Base Rate:
- Logistic A macro AP 0.2172 vs Base Rate 0.2083, but paired ΔAP IC95% crosses zero;
- Logistic A Brier is reliably worse than Base Rate;
- Logistic Lift@10% does not improve;
- CatBoost fails the pre-registered promotion rule and shows repeated segment collapses.

The final T1 champion is therefore a neutral prior:
- DEVELOPMENT prevalence / final probability: **0.2037546**;
- learned calibration: **not promoted** because gains were immaterial;
- ranking capability: **none**.

See `models/lead_quality/MODEL_SELECTION.md` and `FROZEN_MODEL_CONFIG.json`.

## Procedural holdout integrity

The June procedural holdout is **not pristine**. A temporary execution export encoded its labels before the frozen config existed. It was never used for feature/model/calibration selection, but the stricter holdout contract was violated.

The incident is recorded in:
- `models/lead_quality/HOLDOUT_INCIDENT.md`
- `models/lead_quality/artifacts/PROCEDURAL_HOLDOUT_CONSUMED.json`

Any June metric is diagnostic-only. True confirmation requires new/hidden data.

## Pre-P8 gate

`AssessmentSol1/abt/validate_abts.py` still needs to be executed in an environment with the project dependencies, especially Polars, to produce the authoritative P4 runtime manifest:

```bash
python AssessmentSol1/abt/validate_abts.py
```

P7 rebuilt its T1 inputs from raw under the same frozen temporal rules, but that does not substitute for the repository-wide P4 materialization gate. **Prompt 8 must not start until this PASS exists.**

See `evidence/PRE_P8_AUDIT.md` and `audit/PRE_P8_GATE_STATUS.json`.

## Clean-room rule

Never consume historical fitted artifacts from `experimentos/**`: no ABTs, predictions, models, preprocessors, clusterers, target encoders or calibrators.

## Key evidence

- `target/TARGET_CONTRACT.md`
- `splits/SPLIT_CONTRACT.md`
- `abt/ABT_CONTRACT.md`
- `features/FEATURE_REGISTRY.csv`
- `features/ablation_plan.json`
- `evidence/EDA_FINDINGS.md`
- `evidence/DRIFT_FINDINGS.md`
- `evidence/FEATURE_ENGINEERING_DECISIONS.md`
- `models/lead_quality/MODEL_CARD.md`
