# EV-005 — Lead × Spot × Broker

**Estado de evidencia:** empírica, future holdout.

**Experimento:** [entity_profile_match](../entity_profile_match/)

## Evidencia fuente

- [README / reporte](../entity_profile_match/README.md)
- [Resultados JSON](../entity_profile_match/results/results.json)
- [Métricas](../entity_profile_match/results/model_metrics.csv)
- [Combinaciones](../entity_profile_match/results/top_combinations.csv)

## Resultado central

Perfiles + interacciones no mejoran perfiles marginales fuera de muestra:

- delta AUC -0.006, 95% CI [-0.040, +0.023];
- delta AP -0.002, 95% CI [-0.013, +0.009].

## Caveats

- Primera versión de perfiles con clusters muy dominantes en Lead/Spot.
- Algunas combinaciones tienen n pequeño.
- `scheduled_visit` es proxy, no cierre.

**Descubrimiento:** [D005](../conocimiento_agregado/DESCUBRIMIENTOS.md#d005--la-química-lead--spot--broker-no-está-demostrada).
