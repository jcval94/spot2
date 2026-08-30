# MODEL_CARD — Lead Quality T1

## Champion

**BASE_RATE + PLATT**

The score estimates the frozen T1 quantity:

> Probability that the deterministic first inquiry is eventually recorded as `scheduled_visit`, conditional on the T1 information set.

It is **not** final commercial conversion and is not equivalent to T0 or T2.

## Why such a simple champion?

The learned challengers did not produce stable discrimination. Logistic A reached macro AP 0.2172 versus 0.2083 for Base Rate, but the paired AP interval crossed zero, Brier was reliably worse, Lift@10% did not improve and AUC was approximately random. CatBoost also failed its frozen promotion rule.

The assessment gate explicitly prefers the simple solution when lift is not defensible.

## Frozen data contract

- Target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`
- Maturity buffer: 14 days
- Split: `SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30`
- DEVELOPMENT: 4,368 leads
- CALIBRATION: 312 leads
- Model features: **none**
- Raw probability: DEVELOPMENT prevalence = 0.2037546
- Calibrator: Platt, fit only on CALIBRATION
- Final probability: 0.2082788

## Intended operational interpretation

This champion is a **neutral evidence-backed prior**, not a ranking engine. It should not be used to prioritize leads within a cohort because all leads receive the same probability.

If an operational process requires ranking, AssessmentSol1 does **not** provide evidence that the available T1 features support one reliably.

## Challengers retained for evidence

Logistic Regression and CatBoost outputs remain diagnostic evidence only. Logistic coefficients describe associations in an unstable/weak predictor and must not be interpreted causally.

## Known limitations

- `scheduled_visit` is a proxy outcome.
- Strong temporal changes exist in Inventory/Availability coverage, intentionally separated from core LeadQuality.
- The result may reflect a genuinely weak T1 information set, synthetic-data construction, or missing operational signals not present at score time.
- The June procedural holdout is non-pristine because of the documented execution-export incident.
- True confirmation requires new/hidden data.

## Governance

No target, maturity rule, split, feature allowlist or ablation was changed in reaction to results. No new model family was added after observing performance.
