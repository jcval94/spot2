# Entregable 8 — Product Vision

## 1. Principio

La Product Vision no parte de “agregar más modelos”.

Parte de los gaps que quedaron demostrados por la investigación.

La arquitectura actual ya resuelve de forma defendible:

- Lead Quality en T1;
- Inventory Serviceability point-in-time;
- fallback gobernado;
- Opportunity Score lower/upper;
- Semantic Catalog QA desacoplado del predictor.

Los siguientes tres meses deberían concentrarse en cuatro frentes:

1. **instrumentación y versionado**;
2. **outcomes más alineados al producto**;
3. **challengers con evidencia previa real**;
4. **validación causal online**.

---

## 2. Visión de producto

La evolución natural de Spot2 sería pasar de un score estático a un sistema de decisión contextual:

    Lead entra
       |
       v
    T0 — prior / cold-start
       |
    primera inquiry
       |
       v
    T1 — Lead Quality + Inventory Serviceability
       |
       +--> fallback contextual
       |
    nuevas interacciones
       |
       v
    T2 — rescore con trajectory, sólo si pasa gate
       |
       v
    broker / producto actúa
       |
       v
    outcomes instrumentados
       |
       +--> visita
       +--> alternativa aceptada
       +--> cierre
       +--> valor comercial
       |
       v
    aprendizaje causal + retraining gobernado

La prioridad sigue siendo T1. T0/T2 son extensiones, no sustitutos automáticos.

---

## 3. ¿Qué haríamos con tres meses adicionales?

## Mes 1 — Instrumentación y contratos

### Objetivo

Eliminar los gaps que hoy impiden evaluar de forma causal y reconstruir completamente el estado histórico.

### Trabajo

#### A. Versionar el Spot

Crear historial de cambios:

- price_total_mxn_rent;
- price_total_mxn_sale;
- price_sqm;
- area si puede cambiar;
- sector/type;
- geography;
- amenities/attributes;
- is_active;
- copy/title/description.

Cada cambio necesita:

- effective_from;
- effective_to;
- ingested_at;
- source event id.

Esto corrige la principal limitación del matching histórico: hoy la existencia del Spot está controlada, pero varios atributos no tienen versión temporal.

#### B. Availability con timestamp efectivo

Cambiar de snapshot_date date-only a:

- available_effective_at;
- observed_at;
- ingested_at.

Con eso desaparece la ambigüedad de same-day as-of.

#### C. Instrumentar recomendaciones

Por cada exposure:

- recommendation_event_id;
- lead_id;
- spot_id;
- rank;
- score;
- candidate set;
- policy version;
- treatment arm;
- shown_at;
- accepted/rejected;
- broker/user action;
- reason.

Sin exposure logs no puede existir un gold limpio de recommendation relevance.

#### D. Instrumentar outcomes

Solicitar/crear:

- visit_scheduled_at;
- visit_completed_at;
- alternative_accepted_at;
- deal_opened_at;
- deal_closed_at;
- closed_won/lost;
- revenue/commercial value;
- reason lost;
- time-to-stage.

Esto permite dejar de usar scheduled_visit como único proxy.

#### E. Response SLA real

Necesitamos timestamps confiables de:

- inquiry created;
- assigned to broker;
- first broker seen;
- first response;
- first qualified response;
- visit offered;
- visit scheduled.

broker_response_hours actual no es suficiente como SLA limpio.

---

## Mes 2 — Challengers priorizados por evidencia

No todos los experimentos históricos merecen la misma prioridad.

### Prioridad A — T2 / trajectory modeling

Evidencia:

EV-012 encontró señal incremental fuera de muestra concentrada en T2.

Para pooled CatBoost:

- ΔAP T2: +0.0161;
- IC95% [+0.0003, +0.0322].

Para Multi-Head:

- ΔAP T2: +0.0155;
- IC95% [+0.0013, +0.0303].

Conclusión:

**trajectory es el challenger dinámico con evidencia predictiva más concreta.**

Nueva prueba:

- historia estrictamente previa;
- eventos con timestamps efectivos;
- response events sólo si realmente ocurrieron antes del score;
- comparación T2 champion/challenger;
- no mezclar scores T1 y T2.

### Prioridad A — Calibrated Availability

E019 demostró que una P(availability within 30d) es viable temporalmente.

Macro:

- AUC: 0.883;
- Brier: 0.0669;
- Log Loss: 0.192.

No se promueve automáticamente sobre Codexway.

Con mejor historial de Availability, debe re-evaluarse como challenger de:

- serviceability lower/upper;
- prioritización de verificación;
- contextual fallback.

### Prioridad B — Dynamic Need

Evidencia direccional:

- Lift@10 1.108x vs 1.001x;
- ΔLift positivo en punto;
- intervalo cruza cero.

Uso futuro:

- segmentación de intención;
- explicación;
- routing;
- personalización del fallback.

No promover como feature de score sin nueva réplica.

### Prioridad B — Localized Compatibility

Se encontraron pockets locales, incluido DN4 × LOC1 × BSV1 con lift suavizado ~1.510x en su muestra.

Pero:

- hubo múltiples comparaciones;
- el mismo future test participó en discovery;
- no existe confirmación independiente.

Roadmap:

- preregistrar sólo un pequeño número de hipótesis;
- evaluarlas en cohorte nueva;
- usar shrinkage;
- no convertir celdas a multiplicadores post-hoc.

### Prioridad B — Broker Service Profiles

Broker Service sí generó una segmentación balanceada e interpretable.

Su mejora predictiva marginal fue inconclusive.

Uso futuro:

- routing;
- capacidad;
- especialización;
- carga de trabajo;
- strata experimentales.

No usar como multiplicador de Lead Quality.

### Prioridad B — Mejor geografía

La investigación mostró señal preliminar pero cobertura deficiente del market context.

La propuesta de enriquecimiento incluye fuentes y señales de:

- coordenadas;
- accesibilidad;
- densidad económica;
- corredores;
- distancia/tiempo real.

Toda fuente debe tener effective/publication time reproducible.

### Prioridad A/B — Semantic Catalog QA

Mantener:

- Rules-first;
- LLM residual;
- human gold;
- deterministic promotion.

La prioridad no es aumentar uso de tokens.

Es crear un gold humano y medir:

- precision;
- novelty;
- cost por issue validado;
- reviewer workload.

---

## Mes 3 — Shadow, experimentación y producto

### A. Integración real en CRM/queue

La interfaz debe mostrar por lead:

- Lead Quality;
- Inventory Serviceability;
- Inventory Confidence;
- Opportunity lower/upper;
- fallback;
- reason codes;
- freshness;
- acción recomendada.

No mostrar sólo un score opaco.

### B. Shadow scoring

Durante el primer período online:

- no cambiar decisiones;
- registrar score;
- registrar candidate set;
- registrar action que habría recomendado;
- comparar con operación real;
- esperar madurez del outcome.

### C. RCT

Lanzar experimentación sólo después de:

- assignment estable;
- exposure logging;
- outcomes completos;
- SRM checks;
- inventory health checks.

El diseño se detalla en el documento causal.

---

## 4. ¿Cómo integraríamos la solución al producto?

## Superficie para broker/operador

Una tarjeta de oportunidad podría mostrar:

### Calidad del lead

- score;
- band;
- timestamp.

### Estado de inventario

- Serviceable / Potential fallback / Uncertain / Low;
- freshness;
- exact Spot attendable;
- candidate depth.

### Fallback

- hasta K final permitido;
- availability state;
- reason;
- relaxed geography;
- confidence.

### Acción

Ejemplos:

- “priorizar contacto”;
- “verificar inventario primero”;
- “ofrecer alternativa”;
- “workflow estándar”;
- “NO_RESULT — sourcing requerido”.

### Explicabilidad

No generar explanation libre con LLM.

Usar:

- feature/model facts;
- reason codes;
- availability status;
- constraint decisions.

---

## 5. Actualización dinámica del producto

### T0

Con evidencia actual:

- prior poblacional;
- planning;
- no ranking automático.

Antes de revisitarlo necesitamos más señales pre-inquiry.

### T1

Momento principal.

Trigger:

first inquiry persisted.

### T2

Cuando haya una nueva inquiry:

- crear nuevo score event;
- conservar T1;
- usar strict-prior trajectory;
- mostrar explícitamente stage.

### Inventory refresh

Puede actualizarse aunque Quality permanezca fijo.

La UI debe diferenciar:

- score comercial original;
- estado de inventario actual.

---

## 6. Contextual fallback

El fallback futuro puede usar contexto adicional sólo después de instrumentación.

Posibles señales:

- current need;
- Dynamic Need;
- real travel/geographic distance;
- price histórico efectivo;
- availability calibrated;
- broker capacity;
- previous recommendations rejected;
- accepted/rejected reason.

Restricciones duras siguen fuera del learning-to-rank.

El modelo nunca debería aprender a violar:

- modalidad;
- existence PIT;
- inventory policy;
- privacy;
- legal/product constraints.

---

## 7. ¿Qué nuevos datos solicitaríamos?

| Dato | Por qué |
|---|---|
| Precios versionados | budget fit PIT real |
| Historial de cambios del Spot | reconstruir candidate state histórico |
| Effective timestamp de Availability | as-of intradía correcto |
| Availability histórica completa | calibrated availability y drift |
| Exposure de recomendaciones | gold de recommendation evaluation |
| Rank/candidate set mostrado | propensity y causal analysis |
| Acceptance/rejection de alternativa | fallback outcome |
| Visita agendada y completada | outcome intermedio limpio |
| Cierre won/lost | outcome comercial |
| Valor/revenue | optimización económica |
| Timestamps de respuesta | response SLA y trajectory |
| Assignment de broker | routing/interference |
| Broker workload/capacity | guardrail y routing |
| Coordenadas/geocoding | distancia real y localized compatibility |
| Human-gold Catalog QA | precision/recall natural del LLM/rules |
| Copy versionado | semantic QA histórica reproducible |
| Source/publication timestamps externos | geographic enrichment PIT |

---

## 8. Outcome hierarchy futura

No usar un único label para todo.

### Lead Quality

Puede seguir usando un outcome temprano si es operacionalmente útil.

### Product impact

Jerarquía recomendada:

1. lead contacted;
2. qualified response;
3. alternative accepted;
4. scheduled visit;
5. completed visit;
6. opportunity/deal;
7. closed won;
8. commercial value.

Cada modelo/experimento debe declarar cuál nivel intenta optimizar.

---

## 9. Product KPI tree

### North Star propuesta

**Serviceable commercial opportunities per eligible lead.**

No debe adoptarse sin validación con Negocio, pero es más alineada que AUC.

### Drivers

#### Demand

- lead volume;
- lead quality;
- response rate.

#### Inventory

- serviceability;
- fresh coverage;
- candidate depth.

#### Matching

- fallback acceptance;
- recommendation coverage;
- no-result.

#### Execution

- time to first contact;
- broker workload;
- response SLA.

#### Commercial

- completed visits;
- close rate;
- revenue/value.

---

## 10. Qué no haríamos

Durante esos tres meses no recomendaría:

- buscar una arquitectura neuronal más compleja por defecto;
- incorporar LLM features al predictor;
- tuning adicional sobre el holdout consumido;
- promover pockets locales sin cohorte nueva;
- usar current price como histórico;
- evaluar fallback con historical chosen Spot como gold;
- mezclar T1 y T2 scores;
- usar AUC como criterio único;
- automatizar QA semántico sin human gold.

---

## 11. Gates del roadmap

| Candidato | Evidencia actual | Próximo gate |
|---|---|---|
| T0 | débil / exposure drift | nuevos pre-inquiry signals |
| T1 | canónico | forward validation |
| T2 trajectory | positiva en experimentos | réplica en nuevos datos/versiones |
| Dynamic Need | direccional | confirmación temporal |
| Localized compatibility | pockets | preregister + new cohort |
| Broker Service | interpretable, predictive inconclusive | routing experiment |
| Calibrated Availability | fuerte challenger | nueva historia completa + comparison |
| Better geography | propuesta preliminar | PIT enrichment |
| Semantic Catalog QA | supported discovery | human gold |
| Contextual fallback | conceptualmente fuerte | exposure/outcome logs + RCT |

---

## 12. Resultado esperado después de tres meses

No esperaría simplemente “un mejor AUC”.

Esperaría:

1. una plataforma de decisión con lineage;
2. Spot e Inventory versionados;
3. recommendation exposure logs;
4. outcomes comerciales;
5. un T2 challenger limpio;
6. Availability calibrada evaluada contra Codexway;
7. Catalog QA con human gold;
8. uno o más RCTs registrados;
9. evidencia causal sobre ranking/fallback;
10. una base real para decidir qué componentes merecen promoción.

---

## 13. Respuestas directas

### 1. ¿Qué haríamos con tres meses adicionales?

Primero instrumentación, después challengers con evidencia, y finalmente shadow/RCT.

### 2. ¿Cómo integraríamos la solución al producto?

Como una capa de decisión T1 en CRM/queue que conserva Quality, Inventory y Opportunity visibles por separado y actualiza Inventory dinámicamente.

### 3. ¿Qué nuevos datos solicitaríamos?

Versionado de Spot/precios, timestamps efectivos, recommendation exposures, visits, closes, value, full Availability history, broker assignment/workload, response SLA y human semantic gold.

### 4. ¿Cómo mediríamos causalmente impacto?

Con RCT sticky por lead cuando la interferencia sea controlable; si shared broker/inventory produce spillovers materiales, con randomización por clusters/tiempo. El plan completo está en [03_EXPERIMENTACION_CAUSAL.md](03_EXPERIMENTACION_CAUSAL.md).

---

## 14. Trazabilidad

Evidencia principal:

- Codexway README;
- Codexway online A/B protocol;
- EV-007 Geographic Enrichment;
- EV-010 Matching A/B;
- EV-012 Trajectory;
- EV-013 Dynamic Need / Broker Service / local pockets;
- E019 Calibrated Availability;
- Entregable 3 Lead Quality;
- Entregable 4 Inventory;
- Entregables 5/6 Opportunity + Producción;
- AssessmentSol1 LLM closure.
