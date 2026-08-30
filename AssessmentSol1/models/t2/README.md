# T2 Re-scoring — PROMPT 8

Decision: **FUTURE_EXTENSION**.

T2 scores the current second-or-later inquiry at its own `inquiry_at`. Current request payload is allowed; historical state is built only from inquiries with `prior.inquiry_at < current score_time`.

No broker-response history, response hours or accepted-rate feature is used.

The experiment was intentionally limited to:

- `T2_BASELINE`: intake + current request + existing deterministic refinement;
- `T2_TRAJECTORY`: the same model plus the 33 pre-registered strict-prior trajectory features.

Macro temporal-CV results:

| Variant | ROC AUC | AP | Brier | Log Loss |
|---|---:|---:|---:|---:|
| Baseline | 0.4861 | 0.1807 | **0.15247** | **0.48451** |
| + Trajectory | 0.4908 | 0.1857 | 0.15297 | 0.48615 |

Trajectory adds only **+0.0050 AP macro**. AP improves in 3/4 folds, but F1 is negative and the gain is below the pre-registered +0.01 complexity floor. Brier/Log Loss also worsen slightly overall.

Therefore trajectory is a **weak hypothesis confirmed directionally, not a deployable extension**.

Boundary crossing is material: 1,281–1,745 late T2 rows from training-cohort leads are excluded per fold because their current score time is after evaluation start. See `boundary_audit.csv`.
