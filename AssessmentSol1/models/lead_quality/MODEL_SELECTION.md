# MODEL_SELECTION — T1 Lead Quality

**Decision:** `BASE_RATE + PLATT` is the frozen champion.

Target, maturity, split boundaries, FEATURE_REGISTRY and ablation plan were unchanged throughout model selection.

## Development protocol

Four expanding-window folds were used. Selection authority is the macro average of metrics computed **inside each fold**. Independently trained fold probabilities were not globally rank-mixed for selection.

### Macro DEVELOPMENT results

| Variant | ROC AUC | AP | Log Loss | Brier | Lift@10% |
|---|---:|---:|---:|---:|---:|
| Base Rate | 0.5000 | 0.2083 | **0.5120** | **0.1650** | 1.154* |
| Business Rule | 0.5001 | 0.2103 | 0.5276 | 0.1716 | 0.938 |
| Logistic A — intake | 0.5039 | **0.2172** | 0.5257 | 0.1692 | 0.993 |
| Logistic B — + inquiry | 0.5000 | 0.2121 | 0.5291 | 0.1703 | 0.978 |
| Logistic C — + refinement | 0.4942 | 0.2136 | 0.5310 | 0.1709 | 0.994 |
| Logistic D — without asked_visit | 0.4962 | 0.2137 | 0.5305 | 0.1707 | 1.073 |
| Logistic E — selected Spot challenger | 0.4937 | 0.2194 | 0.5327 | 0.1712 | 1.016 |
| CatBoost A | 0.4974 | 0.2097 | 0.5240 | 0.1689 | 0.803 |

*Base Rate has tied probabilities. Its top-k metrics depend on deterministic tie ordering and do **not** represent ranking ability.

## Frozen ablations

A remains the best core learned feature set.

- **A → B:** ΔAP = -0.00510, IC95% [-0.01418, +0.00370]; Brier worsens +0.00103 with IC95% entirely >0.
- **B → C:** ΔAP = +0.00147, IC95% [-0.00728, +0.01066]; below the frozen complexity threshold.
- **asked_visit:** removing it from C changes AP only +0.00018, IC95% [-0.00297,+0.00297]. No evidence justifies special treatment.
- **C → E:** ΔAP = +0.00586, but IC95% [-0.00156,+0.01385]; E remains explicitly challenger-only and does not redefine LeadQuality.

## CatBoost promotion

CatBoost does **not** pass the pre-registered rule versus Logistic A:

- ΔAP = **-0.00754**, IC95% [-0.02976,+0.01352], P(Δ>0)=22.35%.
- ΔBrier = -0.00034, IC95% [-0.00251,+0.00199].
- ΔLift@10% = **-0.190x**, IC95% [-0.480,+0.143].
- CatBoost wins AP in only 2/4 folds.
- Repeated material collapses occur in modality=both, modality=sale, Industrial, Retail and source=organic.

Therefore Logistic is preferred over CatBoost under `MODEL_PROMOTION_RULE.json`.

## Terminal baseline gate

The assessment prompt explicitly says that if no model surpasses the baseline defensibly, the simple solution must be accepted.

Logistic A vs Base Rate:

- ΔAP = +0.00887, but **IC95% [-0.00374,+0.03393] crosses zero**.
- ΔBrier = **+0.00423**, IC95% **[+0.00208,+0.00641]**: proper probability scoring is reliably worse.
- ΔLift@10% = -0.161x, IC95% [-0.343,+0.323].
- Macro ROC AUC = 0.5039.

This is not defensible evidence of ranking lift. The final champion is therefore **Base Rate**, not Logistic A.

This is an evidence-backed neutral result: the delivered T1 information set does not support a reliable learned ranking under the frozen protocol.

## Business rule

The fixed rule was not tuned:

- +2 asked_visit
- +1 urgency ≤30 days
- +1 inquiry completeness ≥0.80
- +1 budget/modality consistency
- +1 requested/original area ratio in [0.80,1.25]

It does not outperform Base Rate.

## Holdout integrity

See `HOLDOUT_INCIDENT.md`. The June procedural holdout was methodologically consumed by an execution-export incident before freeze. It was never used in the decisions above.
