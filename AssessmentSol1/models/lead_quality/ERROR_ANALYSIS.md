# ERROR_ANALYSIS — T1 frozen champion

Champion: **Base Rate + RAW**, probability = **0.2037546** for every row.

Because the champion is constant, conventional per-row ranking error analysis has a special interpretation.

## False positives / false negatives at threshold 0.5

At a 0.5 threshold the champion predicts every row as negative.

On CALIBRATION:
- all positives are false negatives at this threshold;
- there are no false positives;
- this is not a hidden model defect: a constant ~20.4% probability is not designed to produce binary decisions at threshold 0.5.

A production decision threshold would have to come from explicit costs/capacity, not from this assessment.

## High-confidence errors

There are no high-confidence positive predictions. For positive cases the model assigns the same 0.2038 probability as every other case. Therefore row-level “top false positive” narratives would be arbitrary and are intentionally not fabricated.

## Calibration by segment — CALIBRATION

Largest absolute prevalence-minus-prediction gaps among segments with N≥30:

| Segment | N | Observed prevalence | Gap vs 0.20375 |
|---|---:|---:|---:|
| modality=both | ≥30 | 0.2923 | +0.0840 |
| source=referral | ≥30 | 0.1346 | -0.0737 |
| modality=rent | ≥30 | 0.1479 | -0.0604 |
| sector=Retail | ≥30 | 0.1515 | -0.0568 |
| sector=Office | ≥30 | 0.2500 | +0.0417 |
| user_type=tenant_direct | ≥30 | 0.2500 | +0.0417 |

These are diagnostic subgroup deviations, not sufficient evidence to build segment-specific models; doing so now would be a new post-result search.

## Uncertainty cases

All rows have identical model probability. There is therefore no model-derived ordering of “most uncertain” cases. The uncertainty is systemic: the available T1 information did not yield a stable discriminative model.

## Learned-model diagnostic

Logistic A coefficients were inspected only to understand the failed challenger. Some geographic/category coefficients have stable signs across folds, but global AUC≈0.504 and proper scoring is worse than Base Rate. Feature importance or coefficient magnitude is therefore **not** evidence of causality or deployable ranking value.

## Actionable conclusion

Do not manufacture lead-level explanations from a model that the evidence rejected. The proper error-analysis conclusion is that T1 currently supports a calibrated prior, not individual prioritization.
