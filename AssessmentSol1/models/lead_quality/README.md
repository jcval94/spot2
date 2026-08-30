# Lead Quality T1 — PROMPT 7 closed

## Frozen champion

**BASE_RATE + RAW**

Raw score = DEVELOPMENT prevalence: **0.2037546**.  
Final score = **0.2037546** (RAW; learned calibration improvement was immaterial).

This is an evidence-backed neutral prior, not a lead-ranking model.

## Why

No learned model demonstrated defensible superiority under the frozen temporal CV protocol. Logistic A had a modest AP point improvement but its paired IC95% crossed zero, Brier was reliably worse, and Lift@10% did not improve. CatBoost failed the pre-registered promotion rule.

See:
- `MODEL_SELECTION.md`
- `MODEL_CARD.md`
- `CALIBRATION.md`
- `ERROR_ANALYSIS.md`
- `FROZEN_MODEL_CONFIG.json`

## Reproducibility

`train.py`:
- rebuilds DEVELOPMENT features;
- runs Base Rate and the fixed business rule;
- runs Logistic A/B/C/D/E only from the frozen ablation plan;
- selects the core using Logistic;
- trains CatBoost only on the selected core;
- applies paired lead bootstrap;
- applies the terminal baseline gate.

`calibration.py`:
- uses CALIBRATION only;
- compares raw, Platt and eligible isotonic;
- freezes the selected configuration.

`interpretability.py`:
- correctly reports that the frozen champion has no feature importance;
- supports learned-model diagnostic interpretation when a model artifact is supplied.

## Holdout integrity

The June procedural holdout is **not pristine**. A temporary execution export encoded its target before freeze. The incident is recorded in `HOLDOUT_INCIDENT.md` and the holdout is considered consumed.

The stored June predictions/metrics are therefore `DIAGNOSTIC_ONLY_NON_PRISTINE` and cannot change the champion.

## Authoritative outputs

- `metrics/development_fold_metrics.csv`
- `metrics/development_macro_metrics.csv`
- `metrics/bootstrap_comparisons.csv`
- `metrics/calibration_metrics.csv`
- `predictions/champion_development_oof.csv`
- `predictions/calibration_predictions.csv`
- `predictions/procedural_holdout_predictions.csv`

True confirmatory performance requires new/hidden data.
