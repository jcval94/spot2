# E005 — Multi-Head vs especialistas tabulares

## Pregunta

¿La ventaja observada de Modelo 3 proviene realmente de la arquitectura multi-head o puede ser superada por modelos tabulares no lineales, especialmente cuando cada etapa tiene su propio especialista?

## Comparación

Mismo target, población, features y split temporal que E003:

- `multihead_calibrated`: backbone compartido + heads T0/T1/T2.
- `pooled_nn_calibrated`: red única con stage como feature.
- `separate_logistic`: baseline lineal por etapa.
- `specialist_random_forest_calibrated`: RF independiente por etapa.
- `specialist_extra_trees_calibrated`: ExtraTrees independiente por etapa.
- `specialist_lightgbm_calibrated`: LightGBM independiente por etapa.
- `specialist_catboost_calibrated`: CatBoost independiente por etapa.
- `pooled_catboost_calibrated`: un único CatBoost con stage como variable categórica.
- `validation_selected_hybrid`: un modelo por etapa seleccionado exclusivamente con validation AP.

## Principio de comparabilidad

No cambia el problema:

- target: future `scheduled_visit` dentro de 30 días;
- scoring: T0/T1/T2 original;
- censoring: idéntico;
- split: 70/15/15 por cohorte temporal de lead;
- features: idénticas;
- point-in-time joins: idénticos;
- test: no participa en selección de modelo ni calibración.

El **primary change** es únicamente la familia/arquitectura de modelado.

## Métrica primaria

Average Precision macro entre T0/T1/T2.

Secundarias:

- ROC-AUC macro;
- Brier;
- log loss;
- Lift@10%;
- Recall@20%;
- AP/AUC por etapa;
- bootstrap de deltas vs multi-head, remuestreando por `lead_id`.

## Decisión

Se considerará evidencia fuerte contra la superioridad del multi-head si un challenger:

1. mejora macro AP en test; y
2. el IC95% bootstrap del delta macro AP vs multi-head queda por encima de cero.

Una mejora puntual con intervalo que cruza cero se reporta como `INCONCLUSIVE`.

## Outputs

- `results/REPORT.md`
- `results/metrics_by_stage.csv`
- `results/model_ranking.csv`
- `results/bootstrap_deltas_vs_multihead.csv`
- `results/validation_stage_selection.json`
- `results/calibration.json`
- `results/harness_results.json`
- `results/summary.json`
- `results/charts/macro_average_precision.png`
- `results/charts/stage_average_precision.png`
