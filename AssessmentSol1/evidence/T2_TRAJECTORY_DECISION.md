# T2_TRAJECTORY_DECISION — PROMPT 8

Target: `T2_CURRENT_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`.  
Grain: current second-or-later inquiry.  
Score time: current `inquiry_at`.

## Frozen experiment

Only two variants were evaluated:

1. **T2_BASELINE** — frozen lead intake + current inquiry payload + existing deterministic current-vs-intake refinement.
2. **T2_TRAJECTORY** — exactly the same model plus the 33 pre-registered strict-prior trajectory features.

No model zoo, response-history feature, current response, response hours, Inventory, Availability or future interaction feature was opened.

## Temporal validity

- strict-prior history violations: **0**;
- response-history predictors used: **0**;
- future Availability snapshots: **not in the information set**;
- train/validation lead overlap per fold: **0**.

Boundary truncation materially changes the dataset. If lead membership alone had been used, **1,281–1,745 late T2 rows per fold** from training-cohort leads could have crossed the evaluation boundary. They are excluded by the frozen current-score-time rule.

## Results

| Variant | ROC AUC | Average Precision | Brier | Log Loss |
|---|---:|---:|---:|---:|
| T2_BASELINE | 0.4861 | 0.1807 | **0.15247** | **0.48451** |
| T2_TRAJECTORY | 0.4908 | 0.1857 | 0.15297 | 0.48615 |
| Delta | +0.0047 | **+0.0050** | +0.00050 | +0.00164 |

AP delta by fold:

- F1: **-0.0055**
- F2: **+0.0079**
- F3: **+0.0058**
- F4: **+0.0117**

Trajectory improves AP in 3/4 folds, but the macro gain is only +0.0050, below the frozen +0.01 complexity threshold, and proper probability scores slightly worsen.

## Interpretation

The inherited hypothesis **"trajectory may add signal at T2"** receives weak directional support, especially in later folds. AssessmentSol1 does **not** confirm an effect large and stable enough for deployment.

## Decision

**FUTURE_EXTENSION.**

Do not integrate T2 into the principal Opportunity Score now. Retain the trajectory code/registry as a future extension to revisit with richer behavioral events, a cleaner response-event clock and genuinely new temporal data.
