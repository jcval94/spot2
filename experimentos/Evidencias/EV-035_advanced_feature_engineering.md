# EV-035 — Outcome-free advanced Feature Engineering

**Estado:** empírica reproducible / development only.

[E035](../feature_validation/E035_outcome_free_advanced_fe/)

E030 validation/test no se reutilizaron. Se usaron tres folds temporales expansivos dentro de E030 train.

## T0

Ninguna variante muestra señal de desarrollo.

Mejor selección por protocolo: missingness_frequency:

- mean AUC **0.4979**;
- min AUC **0.4741**;
- mean AP/prevalence **0.9865x**;
- min Lift@10 **0.708x**.

Resultado: **NO_DEV_SIGNAL**.

## T1

geo_inventory_relative es la única variante con señal débil:

- mean AUC **0.5001**;
- min AUC **0.4933**;
- mean AP/prevalence **1.0283x**;
- mean Lift@10 **1.0587x**;
- min Lift@10 **0.9756x**;
- sólo 1/3 folds con AUC >0.50.

Resultado: **WEAK_DEV_SIGNAL**, no promoción.

## Lectura

- missingness/frequency y robust bins no rescatan T0/T1.
- T1 parece contener una señal pequeña en la posición relativa del Spot frente al inventario y/o la geografía preferida.
- La señal no es suficientemente estable para abrir un modelo T1.

Fuente: [variant_summary.csv](../feature_validation/E035_outcome_free_advanced_fe/results/variant_summary.csv), [rolling_fold_metrics.csv](../feature_validation/E035_outcome_free_advanced_fe/results/rolling_fold_metrics.csv).


## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
