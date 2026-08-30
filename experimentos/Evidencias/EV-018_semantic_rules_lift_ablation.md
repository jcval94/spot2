# EV-018 — Semantic Rules Lift Ablation

## Estado

**NOT_SUPPORTED for promoting semantic Rules into the scoring ABT**

## Experimento

[`experimentos/semantic_rules_lift_ablation/`](../semantic_rules_lift_ablation/)

Contrato: [experiment_spec.json](../semantic_rules_lift_ablation/experiment_spec.json)

Reporte: [results/REPORT.md](../semantic_rules_lift_ablation/results/REPORT.md)

## Pregunta

¿Las variables semánticas determinísticas obtenidas tras E017 incrementan el **Lift@10%** del ABT canónico E016 en T1/T2?

## Cambio aislado

Mismo:

- target `scheduled_visit_30d`;
- censoring;
- población;
- temporalidad;
- folds;
- CatBoost;
- hiperparámetros.

Único cambio: añadir:

- `rule_direct_conflict_flag`;
- `rule_land_building_copy_flag`;
- `rule_security_ambiguity_flag`;
- `rule_retail_adaptive_use_flag`;
- `rule_semantic_signal_count`;
- `rule_semantic_review_tier`.

T0 no se modifica porque todavía no existe un Spot seleccionado.

## Validación

4 folds temporales expanding-window por cohorte de `lead_id`.

Las métricas se calculan **dentro de cada test fold** y después se promedian.

El bootstrap pareado:

- resamplea `lead_id`;
- lo hace dentro de cada fold;
- calcula el delta de métrica dentro del fold;
- agrega posteriormente.

Esto evita rankear directamente probabilidades de modelos entrenados en folds distintos.

## Resultado

### Cross-validated fold mean

| Scope | Baseline Lift@10% | + Rules Lift@10% | Delta |
|---|---:|---:|---:|
| T1 | 1.199x | 1.136x | **-0.0627x** |
| T2 | 1.336x | 1.256x | **-0.0804x** |
| Macro | **1.267x** | **1.196x** | **-0.0716x** |

Macro:

- ΔLift@10%: **-0.0716x**;
- 95% CI: **[-0.1438, +0.1251]**;
- P(ΔLift > 0): **45.0%**.

Por tanto no existe evidencia para afirmar incremento del lift.

El intervalo cruza cero: E018 tampoco demuestra daño estadísticamente concluyente. La decisión `NOT_SUPPORTED` significa que **no se cumple el gate de promoción**.

### Guardrails

Macro AP:

- baseline: 0.5122;
- Rules: 0.5141;
- delta: **+0.0019**;
- CI: [-0.0153, +0.0167].

Macro AUC:

- baseline: 0.6063;
- Rules: 0.6114;
- delta: **+0.0051**;
- CI: [-0.0087, +0.0188].

La representación semántica puede mover ligeramente métricas suaves en punto, pero no mejora la concentración del top decile.

## Cobertura

Las señales semánticas no son raras: aparecen en **29.8%** de las filas OOF diagnósticas.

T1 muestra asociación descriptiva positiva entre tiers semánticos y target; T2 no conserva esa dirección. Esto es consistente con una señal dependiente de etapa/población, pero no prueba causalidad.

## Decisión

**No incorporar las variables Rules-only al ABT canónico de Lead Quality.**

Mantenerlas para:

- Inventory QA;
- Catalog Quality;
- revisión de inconsistencias;
- priorización de saneamiento de listings.

No seguir buscando subconjuntos de reglas sobre el mismo OOF para rescatar lift: eso introduciría selección post-hoc/multiple testing.

## Corrección metodológica preservada

Un primer run exitoso mezcló raw probabilities entre folds para calcular ranking global. Al detectar diferencias de escala entre modelos/folds, esa evaluación fue descartada.

La corrida autoritativa es:

- workflow: `33297920881`;
- artifact: `9728035555`;
- status: **SUCCESS**.

Trazabilidad: [RUN_HISTORY.md](../semantic_rules_lift_ablation/results/RUN_HISTORY.md).

## Caveats

- listing copy/attributes no están versionados históricamente;
- el target sigue siendo proxy `scheduled_visit`;
- el dataset es sintético;
- el resultado responde a Lead Quality ranking, no al valor operacional de Catalog QA.


## Conocimiento acumulado

Este resultado queda registrado como **D061** en [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
