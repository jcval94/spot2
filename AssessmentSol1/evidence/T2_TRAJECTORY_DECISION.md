# T2_TRAJECTORY_DECISION — Re-scoring challenger

**Decision:** `FUTURE_EXTENSION`.

The inherited hypothesis was:

> trajectory may add signal at T2.

AssessmentSol1 does **not** confirm enough incremental value to recommend deployment.

## Cohort and temporal validity

P4 produces **9,635** model-ready T2 inquiry rows after the frozen maturity/stage-eligibility gate.

For every temporal fold:
- training requires T1 lead membership before the evaluation boundary;
- current T2 `score_time` must also be before the boundary;
- validation requires T1 membership in the validation cohort **and** current T2 score time inside that validation window;
- later interactions never flow backward into training.

Strict-prior trajectory audit: **0 violations**.

Response-history predictors used: **0**.

Broker response fields are used only for target/stage eligibility when their timing is reconstructible; they are never trajectory features.

## Frozen experiment

Only two variants were evaluated:

1. `T2_BASELINE`: safe intake + current inquiry payload + deterministic current-vs-intake context.
2. `T2_TRAJECTORY`: the same baseline plus registered strict-prior trajectory features.

| Variant | Macro ROC AUC | Macro AP | Brier | Log Loss |
|---|---:|---:|---:|---:|
| T2 Baseline | 0.4860 | 0.1864 | **0.15140** | **0.48142** |
| T2 Trajectory | 0.4898 | 0.1896 | 0.15162 | 0.48200 |

Increment:
- ΔAP = **+0.00317**
- ΔAUC = **+0.00380**
- ΔBrier = **+0.00022** (worse)
- ΔLogLoss = **+0.00058** (worse)

### Fold stability

| Fold | ΔAP | ΔAUC | ΔBrier |
|---|---:|---:|---:|
| F1 | -0.00069 | -0.00928 | +0.00055 |
| F2 | +0.00675 | -0.02716 | +0.00139 |
| F3 | -0.00774 | +0.01650 | -0.00015 |
| F4 | +0.01435 | +0.03513 | -0.00090 |

Trajectory improves AP in only **2/4 folds**. The pre-registered rule required at least 3/4 positive folds and macro ΔAP ≥ 0.01.

Those necessary promotion conditions already fail; therefore a bootstrap outcome cannot rescue promotion and no further tuning/model search is warranted.

## Interpretation

Some trajectory quantities can be descriptively meaningful, but the incremental signal is not stable enough to justify:
- additional model complexity;
- per-inquiry state management;
- serving historical aggregations;
- additional monitoring burden.

No response-history feature is recovered.

## Recommendation

Keep T2 as **FUTURE_EXTENSION**. Revisit only if richer event timing, stronger pre-response interaction signals or longer genuine production history becomes available.

Evidence:
- `models/t2/metrics/fold_metrics.csv`
- `models/t2/metrics/macro_metrics.csv`
- `models/t2/metrics/fold_deltas.csv`
