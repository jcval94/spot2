# EV-011 — Rolling temporal CV de arquitectura

**Estado de evidencia:** empírica / final.

**Experimento:** [architecture_cv](../modelo_3/architecture_cv/)

**Parent:** [EV-009 — Multi-Head vs especialistas](EV-009_modelo_3_benchmark_specialists.md)

## Diseño

- 4 folds forward-chaining por cohorte temporal de lead.
- 7,980 snapshots OOF.
- 1,936 leads únicos.
- Todos los snapshots de un lead permanecen juntos dentro de cada fold.
- Test cohorts disjuntos.
- Bootstrap por lead: 700 réplicas.
- Mismo target, scoring point-in-time y features base de E005.

El cambio respecto de E005 es el esquema de validación: rolling temporal CV en lugar de un único holdout.

## Evidencia fuente

- [Reporte](../modelo_3/architecture_cv/results/REPORT.md)
- [Predicciones OOF](../modelo_3/architecture_cv/results/oof_predictions.csv)
- [Métricas OOF](../modelo_3/architecture_cv/results/oof_metrics.csv)
- [Métricas por fold](../modelo_3/architecture_cv/results/fold_metrics.csv)
- [Resumen por fold](../modelo_3/architecture_cv/results/fold_metric_summary.csv)
- [Ranking OOF](../modelo_3/architecture_cv/results/oof_model_ranking.csv)
- [Bootstrap vs Multi-Head](../modelo_3/architecture_cv/results/bootstrap_deltas_vs_multihead.csv)
- [Selección por fold](../modelo_3/architecture_cv/results/fold_stage_selection.json)
- [Summary JSON](../modelo_3/architecture_cv/results/summary.json)
- [Spec](../modelo_3/architecture_cv/experiment_spec.json)
- [Harness record](harness_records/E006_architecture_rolling_cv/record.json)

## Resultado macro OOF

| Modelo | ROC-AUC | AP | Brier | Log loss | Lift@10% |
|---|---:|---:|---:|---:|---:|
| Specialist CatBoost | 0.5820 | 0.4720 | 0.2346 | 0.6611 | 1.23x |
| Specialist Random Forest | 0.5711 | 0.4698 | 0.2363 | 0.6649 | 1.23x |
| Validation-selected hybrid | 0.5734 | 0.4679 | 0.2361 | 0.6642 | 1.20x |
| pooled CatBoost + stage | 0.5721 | 0.4665 | 0.2372 | 0.6669 | 1.19x |
| Multi-Head | 0.5498 | 0.4498 | 0.2386 | 0.6698 | 1.13x |

## Deltas robustos vs Multi-Head

### Specialist CatBoost

- Macro AP: +0.0222, IC95% [+0.0068, +0.0361].
- Macro AUC: +0.0322, IC95% [+0.0197, +0.0461].
- T1 AP: +0.0404, IC95% [+0.0128, +0.0687].
- T1 AUC: +0.0596, IC95% [+0.0342, +0.0858].
- T2 AP: +0.0332, IC95% [+0.0088, +0.0594].
- T2 AUC: +0.0418, IC95% [+0.0191, +0.0671].

### Specialist Random Forest

- Macro AP: +0.0201, IC95% [+0.0078, +0.0321].
- T1 AP: +0.0337, IC95% [+0.0105, +0.0561].
- T1 AUC: +0.0427, IC95% [+0.0181, +0.0691].
- T2 AP: +0.0278, IC95% [+0.0059, +0.0505].
- T2 AUC: +0.0280, IC95% [+0.0073, +0.0491].

### pooled CatBoost + stage

- Macro AP: +0.0167, IC95% [+0.0016, +0.0315].
- Macro AUC: +0.0223, IC95% [+0.0077, +0.0371].
- T1 AP: +0.0270, IC95% [+0.0038, +0.0524].
- T2 AUC: +0.0381, IC95% [+0.0146, +0.0633].
- T2 AP: +0.0229, IC95% [-0.0029, +0.0516] — todavía no robusto.

## Estabilidad fold a fold

La ventaja global de las familias tabulares se conserva, pero la familia seleccionada por validation para cada etapa no es estable:

- T0 alterna ExtraTrees y LightGBM.
- T1 alterna specialist CatBoost y LightGBM.
- T2 alterna pooled CatBoost y specialist CatBoost.

Esto desaconseja usar el híbrido como router definitivo sin más validación temporal.

## Lectura

E006 resuelve la incertidumbre del single holdout E005:

1. Multi-Head ya no es la arquitectura líder.
2. T1 y T2 sí contienen señal que modelos tabulares no lineales explotan mejor.
3. pooled CatBoost + stage es una alternativa única, simple y robusta.
4. Specialist CatBoost tiene el mejor macro AP puntual, pero su ventaja AP directa sobre RF es pequeña y no está demostrada con robustez.

## Caveats

- `scheduled_visit` sigue siendo proxy y no outcome final oculto.
- Datos sintéticos.
- CV temporal evalúa estabilidad histórica, no causalidad.
- El entrenamiento se expande fold a fold por diseño.
- Comparar muchas familias aumenta el riesgo de sobreinterpretar pequeñas diferencias.

## Descubrimientos

- [D019](../conocimiento_agregado/DESCUBRIMIENTOS.md#d019--t1-favorece-especialistas-tabulares-no-lineales)
- [D020](../conocimiento_agregado/DESCUBRIMIENTOS.md#d020--un-solo-catboost-fuerte-con-stage-supera-al-multi-head)
- [D021](../conocimiento_agregado/DESCUBRIMIENTOS.md#d021--t2-favorece-especialistas-tabulares-sobre-el-multi-head)
- [D022](../conocimiento_agregado/DESCUBRIMIENTOS.md#d022--el-híbrido-mejora-pero-su-composición-no-es-estable)
- [D034](../conocimiento_agregado/DESCUBRIMIENTOS.md#d034--rolling-cv-confirma-ventaja-de-modelos-tabulares-sobre-multi-head)
- [D037](../conocimiento_agregado/DESCUBRIMIENTOS.md#d037--el-meta-selector-por-etapa-no-es-estable)


## Evidencia visual añadida

- [PR T0](../modelo_3/architecture_cv/results/charts/pr_curve_t0.svg), [PR T1](../modelo_3/architecture_cv/results/charts/pr_curve_t1.svg), [PR T2](../modelo_3/architecture_cv/results/charts/pr_curve_t2.svg).
- [ROC T0](../modelo_3/architecture_cv/results/charts/roc_curve_t0.svg), [ROC T1](../modelo_3/architecture_cv/results/charts/roc_curve_t1.svg), [ROC T2](../modelo_3/architecture_cv/results/charts/roc_curve_t2.svg).
- [Calibration T0](../modelo_3/architecture_cv/results/charts/calibration_curve_t0.svg), [Calibration T1](../modelo_3/architecture_cv/results/charts/calibration_curve_t1.svg), [Calibration T2](../modelo_3/architecture_cv/results/charts/calibration_curve_t2.svg).
- [Lift/Gains T0](../modelo_3/architecture_cv/results/charts/lift_gains_t0.svg), [T1](../modelo_3/architecture_cv/results/charts/lift_gains_t1.svg), [T2](../modelo_3/architecture_cv/results/charts/lift_gains_t2.svg).
- [AP por fold](../modelo_3/architecture_cv/results/charts/ap_by_fold_macro.svg) y [Lift@10 por fold](../modelo_3/architecture_cv/results/charts/lift10_by_fold_macro.svg).
- [Prevalencia por stage/fold](../modelo_3/architecture_cv/results/charts/positive_rate_by_fold_stage.svg), [Hybrid AP por stage/fold](../modelo_3/architecture_cv/results/charts/hybrid_ap_by_fold_stage.svg) y [Hybrid Lift@10 por stage/fold](../modelo_3/architecture_cv/results/charts/hybrid_lift10_by_fold_stage.svg).

La prevalencia del target no es estacionaria entre folds/stages. Esta variación debe leerse junto con los cambios de AP, Brier y Lift y refuerza la necesidad del esquema temporal de validación.
