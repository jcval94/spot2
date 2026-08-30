# Arquitectura final — Lead Opportunity después del cierre T0/T1

## Principio

La arquitectura final separa tres preguntas distintas:

1. **LeadQuality:** ¿qué tan probable es que el lead produzca una visita futura?
2. **Matching / Routing:** ¿qué Spot o ruta es más coherente con la necesidad observada?
3. **Inventory Serviceability:** ¿el inventario está disponible y suficientemente fresco para ser accionable?

No se obliga a una sola familia de features a resolver las tres preguntas.

## Arquitectura por etapa

### T0 — Lead intake

**LeadQuality:** `NEUTRAL_EVIDENCE_BACKED`.

No hay evidencia robusta de propensión con los campos actuales.

**Capas activas:**

- Search Need;
- modality;
- search specificity/completeness;
- semántica de presupuesto/área;
- atributos del lead.

**Uso permitido:**

- explicación;
- segmentación;
- candidate generation;
- reglas operativas.

**Uso no soportado:**

- ordenar leads por probabilidad de scheduled_visit.

---

### T1 — First inquiry

**LeadQuality:** `NEUTRAL_EVIDENCE_BACKED`.

La señal aparente de T1 original dependía materialmente de clocks/progreso afectados por drift. Dos olas de Feature Engineering no recuperaron señal robusta.

**Capas activas:**

- Dynamic Need;
- Need transition T0→T1;
- Physical profile;
- Location profile;
- Lead×Spot compatibility;
- semantic matching/routing hypotheses.

**Uso permitido:**

- matching;
- routing experimental;
- explicación de intención;
- fallback/serviceability.

**Uso no soportado:**

- propensity ranking T1 con la evidencia actual.

---

### T2 — Engaged lead

**LeadQuality:** `E029_FROZEN_CANDIDATE_PENDING_PROSPECTIVE_GATE`.

Es la única etapa con señal residual defendible después de retirar clocks/progreso y familias inestables.

**Activación productiva requiere:**

- prospective post-freeze gate;
- A/A productivo;
- timestamp real de scheduled_visit;
- manifest final congelado.

---

## Inventory Serviceability

Transversal a T1/T2.

Availability se trata como:

- estado point-in-time;
- freshness/staleness;
- fallback/guardrail.

No se usa como LeadQuality signal sólo porque su cobertura temporal pueda correlacionarse con la target.

---

## LLM

### Ejecutable actualmente

Inventory Semantic Quality.

### Extensión futura

E039 Semantic Inquiry Features, sólo si existe texto real.

El LLM futuro produce:

- message semantics;
- Lead×Spot semantic compatibility;
- intent trajectory.

No produce conversion probability.

---

## Target

Offline:

`target_scheduled_visit_30d`

Ventana:

`(score_time, score_time + 30d]`

Estados:

- POSITIVE;
- NEGATIVE;
- AMBIGUOUS_UNKNOWN_EVENT_TIME;
- RIGHT_CENSORED;
- INELIGIBLE_PRIOR_SCHEDULED_VISIT.

Sólo POSITIVE/NEGATIVE son entrenamiento binario.

---

## ABT

E030.

Grain:

`lead_id × stage × score_time`

Roles:

- model_feature;
- policy_guardrail;
- audit_only;
- identifier;
- target.

Forbidden fields no se materializan.

---

## Política de investigación

La línea T0/T1 está cerrada con el dataset actual.

Se reabre sólo con:

1. información nueva;
2. target nueva;
3. temporalidad point-in-time nueva;
4. cohorte independiente nueva.

No se reabre por más tuning sobre el mismo histórico.
