# EV-006 — Profile clustering benchmark v2

**Estado de evidencia:** empírica, calibración de perfiles congelada + future test.

**Experimento:** [profile_clustering_v2](../profile_clustering_v2/)

## Evidencia fuente

- [README / reporte](../profile_clustering_v2/README.md)
- [Summary JSON](../profile_clustering_v2/results/summary.json)
- [Benchmark de clustering](../profile_clustering_v2/results/clustering_benchmark.csv)
- [Clusterers seleccionados](../profile_clustering_v2/results/selected_clusterers.csv)
- [Interpretabilidad](../profile_clustering_v2/results/profile_interpretability.csv)
- [Métricas](../profile_clustering_v2/results/model_metrics.csv)
- [Bootstrap](../profile_clustering_v2/results/bootstrap_deltas.csv)

## Resultado central

El problema de clusters ~90% se corrige con soluciones seleccionadas cuyo cluster mínimo >=5% y máximo <=70%.

El mejor modelo por AP es E002 Lead Facets (AP 0.215 vs baseline 0.208), pero los intervalos bootstrap de mejora incluyen cero.

E003 Inquiry Intent empeora el resultado respecto a E002.

## Caveats

- Perfiles interpretables no implican automáticamente valor predictivo.
- Compatibilidades residuales son exploratorias.
- Market Context fue excluido por falta de semántica point-in-time suficiente.

**Descubrimiento:** [D006](../conocimiento_agregado/DESCUBRIMIENTOS.md#d006--clustering-balanceado-mejora-perfiles-no-prueba-lift-material).
