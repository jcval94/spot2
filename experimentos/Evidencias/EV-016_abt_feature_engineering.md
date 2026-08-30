# EV-016 — ABT + Feature Engineering point-in-time

## Estado

**IMPLEMENTED / NOT YET BENCHMARKED**

## Experimento

[`experimentos/abt_feature_engineering/`](../abt_feature_engineering/)

Contrato: [experiment_spec.json](../abt_feature_engineering/experiment_spec.json)

Manifest completo: [variable_treatment_manifest.csv](../abt_feature_engineering/variable_treatment_manifest.csv)

Validación: [results/VALIDATION.md](../abt_feature_engineering/results/VALIDATION.md)

## Qué queda implementado

- ABT T0 en `leads.created_at`.
- ABT T1 en primera `inquiry_at`.
- ABT T2 en segunda+ `inquiry_at`, antes de conversión observable.
- target móvil: `scheduled_visit` futuro a 30 días.
- right censoring explícito.
- tratamiento de missing estructural por modalidad.
- logs/ratios/densidades y Dynamic Need T0→T1.
- `spot_age_at_score_days` como sustituto point-in-time de `days_on_market`.
- conteos históricos de Spot reconstruidos desde inquiries, en vez de `spots.total_inquiries`.
- perfiles históricos de Broker as-of, usando `broker_id` sólo como llave.
- Availability por backward as-of.
- Land gate para atributos built-environment.
- amenities JSON → count + 12 multi-hot.
- bloqueo de `lead_score_internal`, current broker response y current-state Spot fields.
- Market Context excluido por default.
- análisis separado de candidatos LLM.

## Corrección adicional del target

EV-010 mostró que `broker_response_hours` no tiene semántica consistente. En particular existen **673 scheduled_visit con response time faltante**.

E016 no supone que esas visitas ocurrieron dentro o fuera del horizonte. Cuando un scheduled_visit sin timestamp puede caer dentro del horizonte de un snapshot:

- `target_scheduled_visit_30d` no se fuerza;
- se marca `label_time_ambiguous=1`;
- la fila se excluye del ABT training-ready.

Las filas dinámicas desde la inquiry que contiene ese scheduled_visit ambiguo también se excluyen, porque no se puede demostrar si la conversión ya había ocurrido al scoring time.

## Validación implementada

Antes de registrar la evidencia:

- Python compile: PASS.
- 9 core unit tests de semántica/leakage: PASS.\n- 1 test repository-aware adicional valida que el manifest cubra exactamente las 86 columnas fuente cuando corre dentro del repo completo.\n- verificación directa post-merge contra headers de `main`: **86/86**, 0 faltantes, 0 extras — PASS.

La ejecución completa sobre datos reales queda automatizada mediante el workflow del experimento.

## LLM

El análisis no recomienda usar un LLM para imputar datos tabulares. Los candidatos actuales son:

1. `spots.title + description` → semantic/cross-field QA;
2. si en el futuro existe raw inquiry text → extracción estructurada de intent/flexibilidad/restricciones.

`message_length` por sí solo no contiene semántica suficiente.

Detalle: [LLM_FEATURE_ANALYSIS.md](../abt_feature_engineering/LLM_FEATURE_ANALYSIS.md)

## Qué NO demuestra

- que el nuevo feature engineering mejore AP/AUC/lift;
- que los features históricos de broker/spot aporten señal incremental;
- que el gating de Land mejore predicción;
- que un feature LLM mejore Lead Quality;
- que Market Context sea point-in-time seguro.

Eso requiere el siguiente benchmark temporal.

## Descubrimientos relacionados

- D025–D033: integridad, availability, missing estructural, response semantics y market context.
- D035–D036: trayectoria T2.
- D050–D055: LLM semantic inventory quality.
- D056–D057: contrato ABT y frontera de features LLM.
