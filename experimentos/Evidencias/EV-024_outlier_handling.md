# EV-024 — Outlier handling train-only

**Estado:** evidencia empírica reproducible.

**Experimento:** [E024](../feature_validation/E024_outlier_handling/)

**GitHub Actions fuente:** https://github.com/jcval94/spot2/actions/runs/33281869820

## Resultado

Eliminar del entrenamiento los flags del Isolation Forest mejora el punto estimado, pero **no de forma robusta**.

Macro:

- keep all AP: **0.5175**;
- drop train anomalies AP: **0.5237**;
- anomaly indicator AP: **0.5221**.

Drop anomalies − keep all:

- ΔAP **+0.0063**, IC95% **[-0.0029, +0.0143]**;
- ΔAUC **+0.0033**, IC95% **[-0.0049, +0.0130]**.

El test y validation nunca se filtraron.

## Interpretación

No hay evidencia suficiente para declarar que las observaciones raras sean ruido dañino. La mejora puntual podría ser real o variación muestral.

Esto confirma la postura conservadora del EDA: Isolation Forest funciona bien como lente de QA, pero no justifica una regla automática de borrado.

## Decisión

- no eliminar outliers automáticamente del release candidate;
- conservar detector como diagnóstico de calidad/segmentación;
- no usar el anomaly flag como driver central: su mejora también es incierta.

## Evidencia fuente

- `E024_outlier_handling/results/bootstrap_delta_vs_keep_all.csv`
- `E024_outlier_handling/results/metrics_by_anomaly_segment.csv`
- `E024_outlier_handling/results/iforest_split_summary.csv`
- harness record E024.


## Descubrimientos relacionados

- [D062](../conocimiento_agregado/DESCUBRIMIENTOS.md#d062--)
- [D071](../conocimiento_agregado/DESCUBRIMIENTOS.md#d071--)
