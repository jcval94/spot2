# Entregable 6 — Escalabilidad y puesta en producción

> ### Lectura en lenguaje claro
> **En una frase:** la propuesta de producción separa modelo, inventario y decisión para poder versionarlos, monitorearlos y revertirlos de forma independiente antes de automatizar.
>
> Algunos nombres técnicos se conservan porque corresponden a métricas o variables reproducibles. **Lift@10** compara el 10% mejor priorizado contra elegir al azar el mismo número de casos; **variable objetivo** es el resultado que se quiere anticipar; **disponible en ese momento / as-of** significa usar sólo información que ya era conocida en ese momento; **muestra de evaluación** es una muestra apartada para evaluación; y **respaldo** es la estrategia de respaldo cuando la opción original no puede recomendarse con suficiente confianza.
>

## 1. Principio de diseño

La arquitectura productiva debe reflejar la arquitectura metodológica, no esconderla.

Calidad del lead e Capacidad del inventario son componentes separados y deben poder evolucionar, fallar, monitorearse y versionarse de forma independiente. Opportunity es una capa de orquestación, no un nuevo modelo que reentrena los dos subsistemas.

Arquitectura lógica:

    Availability snapshots
            |
            v
    Inventory State Store
            |
            v
    Capacidad del inventario ---------
            |                          |
            |                          v
    Lead --> Calidad del lead --> Opportunity Orchestration
                                   |
                                   +--> Quality
                                   +--> Inventory lower/upper
                                   +--> Opportunity lower/upper
                                   +--> respaldo / reason codes
                                   +--> action
                                   |
                                   v
                            Score Store / CRM / Queue

La dirección solicitada queda preservada:

    Lead
    → Calidad del lead
    → Opportunity orchestration
    ← Capacidad del inventario
    ← Availability snapshots

---

## 2. Estado actual vs productización requerida

### Ya existe en Codexway

- contrato T1 explícito;
- modelo stable_segment_logistic;
- calibración Platt;
- variable allowlist;
- Availability backward-as-of;
- respaldo determinista;
- Opportunity lower/upper;
- fingerprints de raw data, variable policy y predictions;
- run manifest reproducible;
- métricas mensuales;
- cambio temporal básico;
- tests de snapshots futuros;
- protocolo A/B sticky por lead_id;
- helper de sample-ratio mismatch;
- gate de validación en paralelo antes de activación.

### Debe implementarse para producción real

- serving API o event consumer;
- variable service operativo;
- snapshot store incremental;
- model registry administrado;
- artifact/container registry;
- latency/load benchmarks;
- alerting y dashboards;
- reversión automatizado;
- canary/shadow routing;
- scheduler/orchestrator;
- schema registry/data contracts;
- decision log inmutable;
- on-call/guía operativa;
- retraining pipeline;
- approval workflow.

La segunda lista es diseño de productización; no se presenta como capacidad ya existente.

---

## 3. Batch vs online

La solución recomendada es híbrida.

| Componente | Modo | Razón |
|---|---|---|
| Calidad del lead T1 | online/event-driven | el momento válido es inmediatamente después de persistir la primera consulta |
| Capacidad del inventario | online sobre estado materializado | necesita responder con el estado conocido más reciente |
| Availability ingestion | incremental/micro-batch | los snapshots cambian independientemente de las consultas |
| Candidate index | batch + incremental | evita escanear todo el catálogo por cada lead |
| Opportunity orchestration | online | combina outputs ya calculados |
| Priority queue | streaming o micro-batch corto | depende de capacidad operativa |
| Métricas de latencia/data quality | casi real-time | detecta fallos operativos |
| Lift/calibration/resultado | batch tras madurez | requiere labels maduras |
| Retraining | batch gobernado | no debe activarse por cada alerta |

---

## 4. Flujo online T1

### Paso 1 — Evento

Se recibe FIRST_INQUIRY_PERSISTED con lead_id, inquiry_id, inquiry_at, payload permitido y correlation id.

inquiry_at es el score_time contractual.

### Paso 2 — Calidad del lead

El servicio:

1. valida schema;
2. reconstruye únicamente variables autorizadas;
3. aplica stable_segment_logistic;
4. aplica calibración Platt;
5. devuelve probabilidad, score, versión del modelo, versión de variable policy y quality band.

No consulta Availability.

### Paso 3 — Inventory

El servicio:

1. recibe necesidad T1 y score_time;
2. recupera Spots elegibles;
3. exige spot.created_at <= score_time;
4. obtiene el último snapshot <= score_time para la decisión histórica;
5. calcula lower/upper, confidence y candidate depth;
6. construye respaldo según el Entregable 4.

Para una decisión operacional posterior puede utilizarse el último snapshot conocido al nuevo decision_time, pero debe guardarse como refresh separado.

### Paso 4 — Opportunity orchestration

Se calcula:

    opportunity_lower = p_quality × serviceability_lower
    opportunity_upper = p_quality × serviceability_upper

y se conservan Quality e Inventory por separado.

### Paso 5 — Persistencia

Se guarda un decision_record inmutable.

### Paso 6 — Operación

Se publica a CRM/queue:

- Calidad del lead;
- Opportunity lower/upper;
- Inventory band;
- confidence;
- acción;
- respaldo;
- vigencia;
- status.

---

## 5. Contrato mínimo del decision record

Cada decisión debe conservar al menos:

- decision_id;
- lead_id;
- inquiry_id;
- stage;
- score_time;
- scored_at;
- p_lead_quality;
- lead_quality_score;
- quality_band;
- inventory_serviceability_lower;
- inventory_serviceability_upper;
- inventory_uncertainty_width;
- inventory_confidence;
- serviceability_band;
- opportunity_probability_lower;
- opportunity_probability_upper;
- opportunity_score;
- priority_band;
- fallback_spot_ids;
- fallback_reason_codes;
- candidate_depth;
- no_result;
- inventory_status;
- quality_model_version;
- calibrator_version;
- inventory_policy_version;
- opportunity_policy_version;
- feature_policy_hash;
- config_hash;
- code_commit_sha o image_digest;
- input schema version;
- availability snapshot references;
- catalog/listing version.

El output nunca debe contener variable objetivo futuro ni intermediario resultado como variable.

---

## 6. variable computation

### Calidad del lead

El modelo final es pequeño, pero el pipeline sigue siendo contractual.

Debe aplicarse la allowlist versionada. No debe existir una lógica de producción equivalente a “si la columna está disponible, úsala”.

### Inventory

Optimización recomendada:

1. pre-indexar Spots por sector, state y modality;
2. mantener latest Availability por spot_id;
3. conservar histórico para audit/backfill;
4. reducir el candidate pool antes de cálculos finos;
5. vectorizar fits;
6. aplicar hard constraints antes del ordenamiento.

El histórico de snapshots no debe reemplazarse por una sola tabla current-state porque se perdería reproducibilidad.

---

## 7. Almacenamiento de Availability

Separar dos vistas.

### Histórica append-only

Campos mínimos:

- spot_id;
- snapshot_date/effective_at;
- ingested_at;
- source_version;
- is_available;
- days_until_available.

Uso:

- backtesting;
- lineage;
- auditoría PIT.

### Latest materialized view

Una fila por Spot con el último estado conocido.

Uso:

- serving operacional.

La vista latest es una optimización; la histórica sigue siendo la autoridad auditora.

### Same-day caveat

El dataset histórico tiene snapshot_date date-only.

Producción debería exigir:

- event_time/effective_at;
- ingested_at;
- SLA/publication semantics.

Así se elimina ambigüedad de snapshots del mismo día.

---

## 8. vigencia

Codexway usa 30 días como lens histórico de vigencia.

Eso no significa que un pipeline productivo deba tardar 30 días en actualizar inventario.

Separar:

- vigencia semántica: edad máxima antes de considerar Inventory incierto;
- ingestion latency: cuánto tarda una actualización de fuente en estar disponible para serving.

Un atraso técnico del pipeline debe generar un incidente propio y no confundirse con un Spot legítimamente stale.

---

## 9. Scoring cadence

### T1

- una vez al persistir la primera consulta;
- idempotente por lead_id + first_inquiry_id + model_version.

### Inventory refresh

Si Availability cambia mientras el lead sigue accionable:

- mantener p_quality_T1;
- recalcular Inventory;
- crear nuevo inventory_refresh_id;
- recalcular Opportunity operacional;
- no sobrescribir el score T1 histórico.

### T2

No activo inicialmente.

Si se promueve:

- nuevo stage;
- modelo/version propios;
- history estrictamente previa;
- métricas separadas;
- no mezclar T1 y T2 como probabilidades equivalentes.

### T0

No usar como ordenamiento operativo con la evidencia actual.

---

## 10. Capacity y queueing

Codexway usa:

- default top 10%;
- escenarios 5%, 10%, 20%.

La implementación debe recibir capacity_n o capacity_pct como input operacional.

No fijar en código un cutoff universal.

Cada re-ordenamiento debe guardar:

- ranking_run_id;
- población elegible;
- capacity;
- score version;
- timestamp;
- tie policy.

---

## 11. Tie handling

El modelo final tiene empates reales.

No usar:

- orden de lectura;
- orden físico de la base;
- sort accidental.

Política recomendada:

1. score descendente;
2. hard operational constraints;
3. si persiste empate, stable randomized hash versionado.

La evaluación offline continúa usando expected fractional capture tie-aware.

---

## 12. Model registry

El registry debe versionar el paquete lógico completo.

### Calidad del lead package

- model binary/coefficient set;
- calibrator;
- variable allowlist;
- transform version;
- training window;
- validation window;
- model card;
- métricas;
- promotion gate;
- code commit;
- dependency lock;
- data fingerprint.

### Inventory policy package

Aunque no sea un modelo ML tradicional:

- vigencia days;
- max respaldo recommendations;
- candidate policy;
- compatibility functions;
- ordenamiento policy;
- hard constraints;
- config hash;
- code version.

### Opportunity policy package

- fórmula;
- band thresholds/validation percentiles;
- capacity defaults;
- two-axis action policy;
- version.

Un cambio en cualquiera crea una nueva versión de decisión.

---

## 13. Versionado

Versionar explícitamente:

- quality_model_version;
- inventory_policy_version;
- opportunity_policy_version;
- schema_version;
- feature_contract_version;
- availability_source_version.

Nunca depender de una etiqueta “latest” como fuente de verdad.

---

## 14. Lineage

Codexway ya genera raw-data fingerprint, variable-policy fingerprint, prediction fingerprint, split manifest y run manifest.

Producción debe extender esa idea al nivel de cada decisión:

    source event
      → normalized payload
      → variable contract
      → model/calibrator
      → p_quality
      → inventory candidate set
      → availability snapshot ids
      → capacidad de atención lower/upper
      → opportunity policy
      → decision
      → CRM action

Debe poder responderse:

> ¿Por qué este lead recibió este score con este inventario a esta hora?

sin reconstrucción manual.

---

## 15. SLO/SLA de diseño

No existe benchmark de serving en la evidencia actual.

Estos valores son objetivos iniciales propuestos, no SLAs medidos.

| Componente | SLO inicial propuesto |
|---|---:|
| Quality scoring p95 | <=150 ms |
| Inventory serving p95 | <=700 ms |
| Opportunity orchestration p95 | <=50 ms |
| End-to-end T1 p95 | <=1 s |
| End-to-end T1 p99 | <=2 s |
| Availability ingestion tras publicación | <=15 min |
| Error rate serving | <0.5% |
| Future-snapshot violations | 0 |
| Known-unavailable respaldo recommendation | 0 |

Antes de fijar un SLA contractual deben ejecutarse load tests, soak tests, peak concurrency, cold-start benchmark y candidate-depth worst case.

---

## 16. Escalabilidad

La parte más costosa es Candidate Generation, no la Logistic.

### Indexar antes de rankear

Evitar scan global de todos los Spots.

### Separar static y dynamic

Static-ish:

- area;
- sector;
- modality;
- geography.

Dynamic:

- Availability;
- snapshot age.

Esto permite cachear candidate pools estructurales y refrescar sólo Availability.

### Vectorización

Calcular fits por batch/vector cuando la escala crezca.

### Cache

La key debe incluir:

- inventory policy version;
- catalog version;
- geography/sector/modality;
- timestamp semantics.

Availability requiere TTL/version; no debe cachearse indefinidamente.

### Backpressure

Si Inventory se degrada:

- Quality puede persistirse;
- Opportunity queda pending/uncertain;
- intake no debe bloquearse indefinidamente;
- operación recibe una acción fail-safe.

---

## 17. Arquitectura de despliegue

Servicios lógicos:

1. Lead Event Service;
2. variable/Contract Service;
3. Calidad del lead Service;
4. Inventory Candidate Service;
5. Availability State Service;
6. Opportunity Orchestrator;
7. Decision Store;
8. Queue/CRM Adapter;
9. Monitoring + Label Maturity Jobs;
10. Registry / despliegue Controller.

No es obligatorio que sean diez microservicios físicos.

Para el volumen inicial pueden desplegarse como 2–3 servicios con módulos internos y contratos claramente separados.

Evitar microservicios prematuros.

---

## 18. Rollout

### Fase 0 — reproducibilidad

- build con lock;
- tests;
- lineage;
- artifact fingerprints;
- sin dependencia LLM para scoring.

### Fase 1 — shadow

- score real;
- no cambiar operación;
- guardar decisiones;
- esperar variable objetivo maturity;
- validar cambio temporal y performance.

### Fase 2 — piloto guardado

Codexway propone:

- 50/50 sticky por lead_id;
- intention-to-treat;
- estratos por sector, source y calendar week.

Tratamiento:

- trabajar leads por Puntaje de oportunidad top-down.

Control:

- ordering actual.

### Fase 3 — expansión

Sólo si:

- no hay SRM;
- performance persiste;
- guardrails pasan;
- Inventory health es suficiente;
- operación acepta el workflow.

---

## 19. Piloto específico de respaldo

Debe medirse separado del ordenamiento general cuando sea posible.

Tratamiento:

- recomendaciones backward-as-of.

Control:

- respaldo actual.

Métrica primaria propuesta por Codexway:

accepted alternative or scheduled visit within 30 days.

Guardrails:

- recommendation latency;
- no-result rate;
- distance relaxation;
- complaint rate.

Esto crea un resultado más alineado con el valor del recomendador.

---

## 20. Retraining

No utilizar retraining puramente calendarizado sin gate.

Cadencia sugerida:

- evaluación mensual al madurar labels;
- revisión trimestral de retraining;
- retraining extraordinario ante cambio temporal/performance breach persistente.

Pipeline:

1. congelar nueva ventana;
2. reconstruir PIT ABT;
3. rolling temporal CV;
4. calibración separada;
5. comparar champion/alternativa evaluada;
6. validar Lift@K;
7. validar Brier/Log Loss;
8. revisar cambio temporal;
9. revisar segment stability;
10. shadow;
11. aprobación.

Reentrenar no significa promover.

---

## 21. reversión

Cada despliegue conserva last-known-good.

Triggers:

- schema incompatibility;
- future snapshot violation;
- NaN/generalized scoring failure;
- artifact/calibrator mismatch;
- data-source outage;
- severe performance degradation confirmada;
- recommendation constraint violation.

reversión por componente:

- Quality → versión previa;
- Inventory policy → versión previa;
- Opportunity policy → versión previa.

No es necesario revertir todo el stack si sólo falló una capa.

---

## 22. Cambios que exigen nueva validación

- variable nueva;
- variable objetivo;
- maturity;
- calibrator;
- vigencia;
- K;
- hard constraint;
- matching;
- fórmula Opportunity;
- T1→T2;
- threshold/capacity policy.

Cambios de dashboards/logging no requieren revalidar el scorer si no alteran la decisión.

---

## 23. Fail-safe por componente

| Fallo | Comportamiento |
|---|---|
| Quality timeout | no inventar score; último score válido sólo si mismo stage/version o workflow estándar |
| Inventory timeout | conservar Quality; marcar Inventory técnicamente no resuelto; no convertir en UNAVAILABLE |
| Availability atrasada | usar estado conocido con vigencia explícita; si excede política, Uncertain/verify |
| Candidate generation falla | TECHNICAL_ERROR, no NO_RESULT |
| Candidate set vacío legítimo | NO_RESULT |
| Registry no disponible | servir versión pinned last-known-good |
| Calibrator faltante | no promover scorer incompleto |
| Orchestrator falla | exponer Quality + Inventory por separado; workflow estándar |
| CRM adapter falla | persistir decisión y reintentar idempotentemente |
| Snapshot futuro detectado | bloquear respuesta de Inventory y alertar crítico |

Distinguir business abstention de technical failure es obligatorio.

---

## 24. Decisión final del Entregable 6

La solución escala mejor como arquitectura modular que como modelo monolítico:

- T1 event-driven;
- Quality online;
- Inventory online sobre snapshots materializados;
- Opportunity como orquestador;
- histórico append-only;
- Inventory refresh sin sobrescribir score histórico;
- shadow → A/B → rollout;
- registry y lineage por componente;
- reversión independiente;
- fail-safe conservador;
- monitoreo multiobjetivo.
