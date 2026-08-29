# EV-009 — Multi-Head vs especialistas tabulares

**Estado de evidencia:** PENDING — experimento implementado; completar con la corrida gobernada.

**Experimento:** [benchmark_specialists](../modelo_3/benchmark_specialists/)

## Evidencia fuente esperada

- [Reporte](../modelo_3/benchmark_specialists/results/REPORT.md)
- [Métricas por etapa](../modelo_3/benchmark_specialists/results/metrics_by_stage.csv)
- [Ranking](../modelo_3/benchmark_specialists/results/model_ranking.csv)
- [Bootstrap vs multi-head](../modelo_3/benchmark_specialists/results/bootstrap_deltas_vs_multihead.csv)
- [Selección por validation](../modelo_3/benchmark_specialists/results/validation_stage_selection.json)
- [Spec](../modelo_3/benchmark_specialists/experiment_spec.json)

## Hipótesis

Un especialista tabular no lineal puede superar al multi-head, especialmente en T2, sin cambiar target, población, features ni split.

## Leakage / comparabilidad

Se hereda el pipeline point-in-time de E003. El único cambio primario es la familia de modelado.

**Descubrimiento:** pendiente de la corrida.
