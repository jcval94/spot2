# Contrato de la ABT definitiva

## Unidad analítica

La ABT no es una fila por lead estático. Es una fila por **decisión de scoring**.

```
prediction_key = lead_id | stage | score_time | inquiry_id-or-T0
```

Esto permite que un mismo lead cambie de estado al entrar una inquiry nueva sin contaminar splits.

## Target

La única target binaria permitida es:

`target_scheduled_visit_30d`

según E028:

- 1: scheduled_visit conocido en `(score_time, score_time+30d]`;
- 0: 30 días maduros sin evento conocido/ambiguo en la ventana;
- ambiguous: excluido;
- right-censored: excluido;
- visita previa conocida: snapshot ineligible.

## Split

1. construir y etiquetar todos los snapshots;
2. seleccionar rows POSITIVE/NEGATIVE;
3. obtener leads con al menos una row model-ready;
4. ordenar esos leads por `created_at, lead_id`;
5. 70% train / 15% validation / 15% test;
6. todas las rows de un lead permanecen en el mismo split.

Los leads sin ninguna row madura/observable quedan `unlabeled_future` en la tabla de auditoría.

## Feature policy

### Model features

Se toma exactamente `E029/results/feature_policy.json`.

No entran al modelo:

- clocks de calendario/progreso;
- `prior_searches`;
- Availability;
- broker prior;
- current-state Spot fields inseguros;
- Market Context sin effective/publication time.

### Policy guardrails

La ABT sí conserva Availability point-in-time como contexto operacional:

- estado as-of;
- days_until_available;
- competing inquiries;
- snapshot age;
- stale >90d;
- effective known/current state.

Estas columnas **no** son LeadQuality features.

### Audit-only

Se preservan variables útiles para QA/drift:

- `score_weekday`, `score_hour`, `score_month`;
- `days_from_lead_creation`;
- `inquiry_number`;
- `days_since_first_inquiry`;
- `prior_searches`.

Su presencia en la ABT no autoriza su uso predictivo.

## Forbidden

El build falla si intenta materializar como feature:

- `lead_score_internal`;
- `broker_response`;
- `broker_response_hours`;
- `response_event_at`;
- `first_conversion_at`;
- `spot_days_on_market`;
- `spot_total_views`;
- `spot_total_inquiries`;
- `spot_is_active`.

## Pesos

`sample_weight_stage_lead` se calcula por split:

- cada lead reparte peso entre sus snapshots de la misma etapa;
- las etapas quedan balanceadas dentro de cada split.

Es metadata de entrenamiento, no feature.

## Criterio de validez

La ABT sólo es válida si:

- prediction_key es único;
- ningún lead cruza splits;
- train < validation < test temporalmente;
- model-ready contiene sólo target 0/1 observada;
- audit conserva censura/ambigüedad;
- no existen forbidden columns;
- la lista de model_feature coincide con E029.
