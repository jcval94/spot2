# Visualizaciones Fase 3 — curvas, CV temporal y heatmaps reales

Esta fase materializa **19 imágenes SVG reales** a partir de resultados empíricos ya versionados. No sustituye las métricas tabulares: las hace inspeccionables visualmente.

## 1. Precision–Recall por stage

### T0
![PR T0](../modelo_3/architecture_cv/results/charts/pr_curve_t0.svg)

Fuente: `modelo_3/architecture_cv/results/oof_predictions.csv`.

### T1
![PR T1](../modelo_3/architecture_cv/results/charts/pr_curve_t1.svg)

### T2
![PR T2](../modelo_3/architecture_cv/results/charts/pr_curve_t2.svg)

---

## 2. ROC por stage

### T0
![ROC T0](../modelo_3/architecture_cv/results/charts/roc_curve_t0.svg)

### T1
![ROC T1](../modelo_3/architecture_cv/results/charts/roc_curve_t1.svg)

### T2
![ROC T2](../modelo_3/architecture_cv/results/charts/roc_curve_t2.svg)

Fuente: `modelo_3/architecture_cv/results/oof_predictions.csv`.

---

## 3. Calibration / reliability

### T0
![Calibration T0](../modelo_3/architecture_cv/results/charts/calibration_curve_t0.svg)

### T1
![Calibration T1](../modelo_3/architecture_cv/results/charts/calibration_curve_t1.svg)

### T2
![Calibration T2](../modelo_3/architecture_cv/results/charts/calibration_curve_t2.svg)

Las curvas usan deciles de score OOF y comparan contra la diagonal ideal.

---

## 4. Lift y cumulative gains

### T0
![Lift gains T0](../modelo_3/architecture_cv/results/charts/lift_gains_t0.svg)

### T1
![Lift gains T1](../modelo_3/architecture_cv/results/charts/lift_gains_t1.svg)

### T2
![Lift gains T2](../modelo_3/architecture_cv/results/charts/lift_gains_t2.svg)

Cada imagen muestra gains acumulados y lift acumulado sobre el ranking OOF.

---

## 5. Average Precision por fold temporal

### Rolling temporal CV
![AP rolling CV](../modelo_3/architecture_cv/results/charts/ap_by_fold_macro.svg)

Fuente: `modelo_3/architecture_cv/results/fold_metrics.csv`.

### Trajectory temporal CV
![AP trajectory CV](../modelo_3/trajectory_cv/results/charts/ap_by_fold_macro.svg)

Fuente: `modelo_3/trajectory_cv/results/fold_metrics.csv`.

---

## 6. Lift@10% por fold temporal

### Rolling temporal CV
![Lift10 rolling CV](../modelo_3/architecture_cv/results/charts/lift10_by_fold_macro.svg)

### Trajectory temporal CV
![Lift10 trajectory CV](../modelo_3/trajectory_cv/results/charts/lift10_by_fold_macro.svg)

---

## 7. T0 → T1 transition heatmap

![Need transition heatmap](../matching_profiles_v4/results/charts/need_t0_t1_transition_heatmap.svg)

Fuente: `matching_profiles_v4/results/need_t0_t1_transition_matrix.csv`.

La intensidad representa probabilidad de transición normalizada por perfil T0.

---

## 8. Dynamic Need × Broker Service

![Dynamic Need x Broker Service](../matching_profiles_v4/results/charts/dynamic_need_x_broker_service_heatmap_lift.svg)

Fuente: `matching_profiles_v4/results/top_service_compatibility_cells.csv`.

- Color: lift suavizado vs tasa global.
- Anotación: lift y soporte `n`.
- Celda gris: combinación con soporte menor al gate `n < 50`; no se interpreta como lift 0.

---

## 9. Need Transition × Physical Profile

![Need Transition x Physical](../matching_profiles_v4/results/charts/need_transition_x_physical_heatmap_lift.svg)

Fuente: `matching_profiles_v4/results/top_compatibility_cells.csv`.

- Color: lift suavizado vs tasa global.
- Anotación: lift y soporte `n`.
- Celdas sin soporte mínimo permanecen explícitamente como `n < 50`.

---

## Modelos comparados

Las curvas de Modelo 3 comparan:

1. Specialist Random Forest.
2. Specialist CatBoost.
3. Validation-selected Hybrid.
4. Pooled CatBoost.
5. Multihead.

Las curvas PR, ROC, calibration y lift/gains se calculan sobre **predicciones OOF temporales**, no desde métricas agregadas.

## Alcance

Estas figuras son evidencia descriptiva/predictiva del backtest. No convierten los resultados offline en evidencia causal ni eliminan las caveats registradas en EV-011, EV-012 y EV-013.
