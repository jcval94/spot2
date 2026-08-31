# T2 Re-scoring

Status: **FUTURE_EXTENSION**.

Only `T2_BASELINE` and `T2_TRAJECTORY` were evaluated.

Macro AP:
- baseline: **0.1864**
- trajectory: **0.1896**
- ΔAP: **+0.0032**

Trajectory improves AP in only **2/4 folds**, below both frozen promotion requirements (ΔAP ≥ 0.01 and ≥3 positive folds). Proper probability scores are also slightly worse overall.

Temporal audit:
- strict-history violations: **0**
- response-history predictive features: **0**
- model-ready T2 rows: **9,635**

Do not deploy T2 trajectory scoring now.

See:
- `../../evidence/T2_TRAJECTORY_DECISION.md`
- `metrics/fold_metrics.csv`
- `metrics/fold_deltas.csv`
- `train.py`
