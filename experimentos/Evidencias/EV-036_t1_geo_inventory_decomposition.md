# EV-036 — T1 geo/inventory decomposition

**Estado:** NO_DEV_SIGNAL.

[E036](../feature_validation/E036_t1_geo_inventory_decomposition/)

Se descompuso la pista débil de E035 usando sólo E030 train y rolling folds.

- atomic mean AUC: **0.4896**;
- geo_distance: **0.4842**;
- inventory_relative: **0.4818**;
- inventory_plus_geo: **0.4887**;
- inventory_geo_frequency: **0.4820**.

Ninguna variante obtiene AUC >0.50 en un fold. inventory_plus_geo alcanza AP/prevalence medio 1.005x y Lift@10 medio 0.996x, insuficiente.

**Conclusión:** la señal débil E035 no se sostiene al aislar componentes; no promover geo/inventory features a T1 LeadQuality.

Fuente: [summary.csv](../feature_validation/E036_t1_geo_inventory_decomposition/results/summary.csv).


## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
