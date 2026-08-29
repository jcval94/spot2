# EV-005 — Lead × Spot × Broker

**Estado de evidencia:** empírica legacy; metodología superseded por EV-006.

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

- `profile_clustering_v2` identificó look-ahead en la construcción histórica del perfil de broker de esta primera versión; por ello no debe tratarse como evidencia gobernada definitiva.
- La metodología corregida está en [EV-006](EV-006_profile_clustering_v2.md).
- Primera versión de perfiles con clusters muy dominantes en Lead/Spot.
- Algunas combinaciones tienen n pequeño.
- `scheduled_visit` es proxy, no cierre.

**Descubrimiento:** [D005](../conocimiento_agregado/DESCUBRIMIENTOS.md#d005--la-química-lead--spot--broker-no-está-demostrada).
