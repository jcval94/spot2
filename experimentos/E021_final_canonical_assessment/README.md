# E021 — Final canonical assessment benchmark

## Objective

Close the three remaining modeling gaps of the assessment on one authoritative point-in-time generation:

1. benchmark the canonical PIT Feature Engineering layer;
2. rerun Lead Opportunity Score + fallback end-to-end with the canonical OOF Lead Quality score;
3. produce explicit OOF error analysis for the final Lead Quality model.

## Data contract

E021 rebuilds its modeling rows directly from `data/candidate/` through the canonical E016 builder. It does not use historical ABTs as model input.

Scoring points:

- T0 = `lead.created_at`;
- T1 = deterministic first inquiry;
- T2 = second and later inquiry while no conversion is already observable.

Target: future `scheduled_visit` within 30 days, with right censoring and ambiguous event time exclusions inherited from E016.

## Comparison

- `pooled_catboost_pit_core`: minimal leakage-safe business variables.
- `pooled_catboost_pit_full`: complete E016 PIT feature contract.

Both use the same four rolling lead-cohort folds and stage-wise Platt calibration.

## End-to-end

The canonical full OOF score is injected into the governed E020 logic:

`LOS = P_quality × P_inventory_top3`

Fallback keeps the frozen bounded top-3 policy.

## Error analysis

For T1/T2, errors are defined at the stage-relative P85 operational capacity gate. Results are segmented by stage, sector, modality, user type and availability state, plus concrete FP/FN examples.

## Outputs

- `results/oof_predictions.csv`
- `results/fold_metrics.csv`
- `results/cv_mean_metrics.csv`
- `results/paired_bootstrap.csv`
- `results/error_analysis_summary.csv`
- `results/error_examples.csv`
- `results/end_to_end/*`
- `results/REPORT.md`
- `results/summary.json`

The experiment is decision-ready only after the workflow completes successfully and the generated evidence is reviewed.
