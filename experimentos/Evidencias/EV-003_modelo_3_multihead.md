# EV-003 — Modelo 3 multi-head

**Estado de evidencia:** empírica, validación temporal por cohortes de lead.

**Experimento:** [modelo_3](../modelo_3/)

## Evidencia fuente

- [Resumen](../modelo_3/results/summary.md)
- [Resumen JSON](../modelo_3/results/summary.json)
- [Métricas por etapa](../modelo_3/results/metrics_by_stage.csv)
- [Spec](../modelo_3/experiment_spec.json)
- [Código](../modelo_3/run_experiment.py)

## Resultado central

Multi-head vs pooled:

- macro AP: 0.5083 vs 0.4968, delta +0.0115;
- macro AUC: 0.5330 vs 0.5266, delta +0.0064.

T2 multi-head: AUC 0.595, AP 0.515, Lift@10% 1.39x.

## Caveats

- Target proxy `scheduled_visit`.
- Datos sintéticos.
- La evidencia respalda una arquitectura predictiva para este dataset, no una afirmación causal.

**Descubrimiento:** [D003](../conocimiento_agregado/DESCUBRIMIENTOS.md#d003--shared-backbone--heads-por-etapa-sí-aporta).
