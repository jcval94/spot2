# EV-004 — Interpretabilidad T2

**Estado de evidencia:** empírica, permutation importance sobre test temporal.

**Experimento:** [interpretabilidad_t2](../modelo_3/interpretabilidad_t2/)

## Evidencia fuente

- [Reporte](../modelo_3/interpretabilidad_t2/results/REPORT.md)
- [Family importance](../modelo_3/interpretabilidad_t2/results/family_importance.csv)
- [Robustez](../modelo_3/interpretabilidad_t2/results/family_importance_robustness.csv)
- [Permutation multi-head](../modelo_3/interpretabilidad_t2/results/multihead_permutation_importance.csv)
- [RF permutation](../modelo_3/interpretabilidad_t2/results/rf_permutation_importance.csv)
- [Direccionalidad](../modelo_3/interpretabilidad_t2/results/directionality.csv)

## Resultado central

`interaction_history` es la familia dominante: ΔAP +0.0638 y ΔAUC +0.0720 al romperla en test.

La dominancia persiste usando primer y último T2 por lead.

## Caveats

- Importancia predictiva no es efecto causal.
- Variables correlacionadas pueden repartirse señal.
- Concordancia de ranking multi-head vs RF es baja/modesta.

**Descubrimiento:** [D004](../conocimiento_agregado/DESCUBRIMIENTOS.md#d004--t2-obtiene-su-señal-principalmente-de-historia-observable).
