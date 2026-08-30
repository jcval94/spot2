# AssessmentSol1 — clean-room definitive assessment

Status: **PROMPT 8 COMPLETE. T1 remains frozen; T0 is neutral; T2 is future extension. Next: Inventory / Fallback / Opportunity Score.**

This directory is the only writable home for the definitive Spot2 assessment. Historical experiments may be read as prior evidence but are never runtime dependencies.

## Frozen foundations

- raw/source audit: complete;
- temporal semantics: frozen;
- primary target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`;
- T1 maturity: 14 days;
- split contract: `SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30`;
- point-in-time ABT architecture: independently revalidated from raw;
- feature registry / ablation plan: frozen;
- T1 champion: **BASE_RATE + RAW**, p = **0.2037546**, no ranking capability.

## P4 runtime-equivalence gate

`abt/artifacts/p4_qa_summary.json` now reports **PASS** from an independent raw-data reconstruction of the frozen P4 grains and temporal gates.

It reproduces:
- T0 audit/model-ready: 5,000 / 4,710;
- T1: 5,000 / 4,953;
- T2: 17,576 / 9,635;
- Inventory candidate universe: 1,114,990 logical rows;
- selected future Spots: 0;
- future Availability snapshots: 0.

The exact Polars builder code path remains a **non-blocking final reproducibility follow-up** because this runtime lacks Polars. P8 does not consume P3/P4 materialized feature tables; it reconstructs stage data directly from raw under the frozen contracts.

## P7 — T1 principal product

No learned T1 model demonstrated defensible superiority to Base Rate. The final Lead Quality output is therefore:

**BASE_RATE + RAW = 0.2037546**

It is a neutral probability prior, not an individual ranking score.

The June procedural holdout remains permanently non-pristine and diagnostic-only.

## P8 — stage sensitivity

### T0
Decision: **NEUTRAL_EVIDENCE_BACKED**.

T0 estimates a different quantity from T1. Intake-only Logistic does not provide stable discrimination:
- macro AP 0.4803 → 0.4831;
- macro AUC 0.4934;
- Brier and Log Loss worsen.

T0 should not deploy a predictive ranking model.

### T2
Decision: **FUTURE_EXTENSION**.

Adding the 33 strict-prior trajectory features gives:
- AP 0.1807 → 0.1857;
- delta AP +0.0050;
- 3/4 folds positive;
- Brier / Log Loss slightly worse.

The effect is below the frozen +0.01 complexity gate. No T2 predictive model is recommended now.

## Stage product decision

- **T0:** cold-start prior only;
- **T1:** principal Lead Quality product, neutral prior only;
- **T2:** future re-scoring extension, not deployed.

Do not average T0/T1/T2 probabilities. T0 has a different target, while T2 conditions on a different stage population.

## Clean-room rule

Never consume historical fitted artifacts from `experimentos/**`: no ABTs, predictions, models, preprocessors, clusterers, target encoders or calibrators.

## Key evidence

- `target/TARGET_CONTRACT.md`
- `splits/SPLIT_CONTRACT.md`
- `abt/ABT_CONTRACT.md`
- `features/FEATURE_REGISTRY.csv`
- `models/lead_quality/MODEL_CARD.md`
- `evidence/T0_EXPOSURE_DRIFT.md`
- `evidence/T2_TRAJECTORY_DECISION.md`
- `evidence/STAGE_COMPARISON.md`
- `models/P8_EXECUTION_MANIFEST.json`
