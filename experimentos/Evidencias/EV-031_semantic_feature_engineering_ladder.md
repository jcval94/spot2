# EV-031 — Semantic Feature Engineering ladder

**Estado:** empírica reproducible; development selection.

[E031](../feature_validation/E031_semantic_feature_engineering_ladder/)

Cinco variantes se compararon con Random Forest fijo usando sólo train/validation: atomic, scale/specificity, semantic Need, soft profiles y semantic interactions.

### T0 validation

N=694, prevalence 49.71%.

Mejor variante según protocolo: **soft_profiles**, pero no calificó el gate:

- AUC **0.4678**;
- AP **0.5004**;
- AP/prevalence **1.0065x**;
- Lift@10 **1.092x**.

### T1 validation

N=691, prevalence 50.80%.

Mejor variante: **semantic_interactions**, tampoco calificó:

- AUC **0.5010**;
- AP **0.5195**;
- AP/prevalence **1.0228x**;
- Lift@10 **1.097x**.

Por diseño E031 no utilizó test para seleccionar.

Fuente: [validation_ladder.csv](../feature_validation/E031_semantic_feature_engineering_ladder/results/validation_ladder.csv).


## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
