# Monitoreo, gobierno, retraining y guía operativa

> ### Lectura en lenguaje claro
> **En una frase:** el sistema debe vigilar por separado datos, calidad del lead, inventario, puntaje, operación y resultados; una métrica estable no garantiza que todo esté sano.
>
> Algunos nombres técnicos se conservan porque corresponden a métricas o variables reproducibles. **Lift@10** compara el 10% mejor priorizado contra elegir al azar el mismo número de casos; **variable objetivo** es el resultado que se quiere anticipar; **disponible en ese momento / as-of** significa usar sólo información que ya era conocida en ese momento; **muestra de evaluación** es una muestra apartada para evaluación; **shadow** es una ejecución en paralelo que todavía no cambia decisiones reales; y **respaldo** es la estrategia de respaldo cuando la opción original no puede recomendarse con suficiente confianza.
>

## 1. Principio

Un sistema de priorización puede fallar aunque AUC permanezca estable.

Se monitorean por separado:

1. salud de datos;
2. Calidad del lead;
3. Inventory;
4. Opportunity;
5. ordenamiento/capacidad;
6. serving;
7. resultados;
8. estabilidad por segmentos.

---

## 2. Baselines canónicos

Son referencias históricas de Codexway, no thresholds eternos.

### Calidad del lead — muestra histórica de evaluación

- base rate: **21.22%**;
- ROC-AUC: **0.5478**;
- PR-AUC: **0.2391**;
- Brier: **0.1658**;
- Lift@10: **1.689x**;
- Recall@10: **16.98%**.

### Opportunity lower

- PR-AUC: **0.2477**;
- Lift@10: **1.370x**;
- Recall@10: **13.77%**;
- Brier: **0.1707**.

### Inventory

- mean capacidad de atención lower: **0.6936**;
- upper: **0.8213**;
- uncertainty width: **0.1277**;
- inventory confidence: **0.5217**;
- exact attendable: **45.64%**;
- exact unknown: **44.30%**;
- no known alternative: **2.38%**.

### vigencia 30d

- fresh candidate share: **57.09%**;
- unknown/stale: **42.91%**;
- leads con algún candidato fresco: **98.34%**.

---

## 3. Base rate

Medir al madurar labels:

- global;
- mes;
- sector;
- modality;
- source;
- company size;
- priority band.

La evidencia mensual de Codexway en 2026 muestra positive rates aproximadamente entre 19.7% y 23.7%.

Cambios de base rate afectan calibration, precision, workload e interpretación del Lift.

No diagnosticar model cambio temporal antes de separar label-mix cambio temporal.

---

## 4. Score distribution

Monitorear:

- mean/median;
- p05/p25/p50/p75/p95;
- share por band;
- ties;
- resolución;
- saturación.

Por separado:

- p_lead_quality;
- Opportunity lower;
- Opportunity upper;
- Inventory lower/upper.

Una distribución estable con performance degradada sugiere concept cambio temporal. Una distribución desplazada con performance estable puede reflejar population cambio temporal o instrumentación.

---

## 5. Lift@K y capacidad

Reportar:

- Lift@5/10/20;
- Recall@5/10/20;
- Precision@5/10/20.

Separar:

- objetivo Quality;
- objetivo serviceable/joint cuando exista label alineado.

Medir siempre al capacity realmente usado y conservar 5/10/20 como referencia.

---

## 6. Calibration

Para Calidad del lead:

- Brier;
- Log Loss;
- calibration curve;
- observed vs predicted por bin;
- intercept/slope si se implementa.

Opportunity no debe forzarse a interpretarse como probabilidad conjunta si sigue siendo un score operacional.

---

## 7. variable cambio temporal

El modelo final es de baja dimensión, pero debe monitorearse:

- share Industrial;
- share small;
- share paid;
- share de industrial_small_or_paid_interaction;
- ausencia de datos;
- schema violations.

Codexway ya reporta PSI para la interacción.

En futuras versiones más ricas:

- PSI/JS/SMD según tipo;
- conditional ausencia de datos;
- cardinalidad;
- categorías nuevas.

---

## 8. ausencia de datos

Separar:

- applicable missing;
- structural/not applicable;
- malformed;
- source absent.

Por campo y segmento.

Alertar cambios abruptos, categorías nuevas, nulls en required y conversiones de tipo.

---

## 9. Inventory monitoring

### Availability coverage

Medir:

- candidates con prior snapshot;
- candidates fresh;
- leads con al menos un fresh candidate;
- exact Spot coverage.

La evidencia histórica muestra coverage cambio temporal fuerte. Es un KPI de inventario/instrumentación, no automáticamente Calidad del lead cambio temporal.

### Snapshot age

- p50/p90/p95;
- <=7d;
- <=30d;
- <=90d;
- >90d;
- no prior snapshot.

### Availability state

- available now;
- within urgency;
- known unavailable;
- unknown missing;
- unknown stale.

### Candidate depth

- mean/median/p90;
- leads con 0;
- candidates por tier;
- candidates después de hard constraints.

AssessmentSol1 encontró candidate-depth cambio temporal fuerte; debe tratarse como exposición/catálogo.

---

## 10. respaldo monitoring

Reportar:

- Coverage@1;
- Coverage@3;
- Coverage@5;
- full-list Coverage@3;
- full-list Coverage@5;
- candidate depth;
- UNKNOWN/VERIFY share;
- NO_RESULT rate;
- known-unavailable recommendation rate;
- future-spot violation rate;
- future-snapshot violation rate;
- distance relaxation;
- respaldo acceptance cuando exista.

No negociables:

- future snapshot violations = 0;
- known unavailable recomendado como confirmado = 0.

Hit@K histórico no es KPI principal mientras no exista gold de recommendation relevance.

---

## 11. capacidad de atención rate

Monitorear:

- exact attendable;
- respaldo attendable;
- Serviceable;
- Potential respaldo;
- Uncertain;
- Low capacidad de atención.

Cruzar Quality × Inventory:

- High Quality × Serviceable;
- High Quality × Uncertain;
- High Quality × Low capacidad de atención;
- Standard × Serviceable.

Esto hace visible el trade-off que un score único puede ocultar.

---

## 12. Opportunity monitoring

### Core

- lower distribution;
- upper distribution;
- uncertainty width;
- priority-band share.

### Delta vs Quality

En cada cohorte madura:

- ΔLift@K;
- ΔRecall@K;
- overlap top-K;
- conversion positives;
- serviceable positives;
- joint positives cuando exista label válido.

### Guardrail

Si Opportunity mejora capacidad de atención pero deteriora conversion proxy, reportar ambos valores.

Nunca esconder uno dentro de una métrica compuesta.

---

## 13. Frecuencia

| Métrica | Frecuencia |
|---|---|
| schema/error/latency | minutos |
| Availability ingestion | minutos |
| vigencia/coverage/candidate depth | hora/día |
| score distribution | día |
| capacity volumes | día |
| variable cambio temporal | semana |
| respaldo metrics | semana |
| base rate | tras madurez |
| Lift/calibration | mensual tras madurez |
| retraining review | trimestral o trigger |

---

## 14. Alertas iniciales

Son propuestas operativas, no thresholds validados por el reto.

### Critical

- future snapshot violation >0;
- known-unavailable recommended >0;
- schema incompatible;
- artifact mismatch;
- scoring pipeline unavailable;
- tasa relevante de scores inválidos.

### Warning

- fresh coverage cae >10 pp vs baseline móvil;
- leads con algún fresh candidate <95%;
- p95 snapshot age cruza persistentemente 30d;
- score distribution cambia bruscamente;
- base rate cambia >3 pp;
- NO_RESULT >2x su baseline estable;
- p95 latency supera SLO en dos ventanas consecutivas.

Usar ventanas persistentes para evitar alertas por ruido.

---

## 15. Observabilidad

Cada request emite logs estructurados.

### Quality log

- request id;
- lead/consulta;
- model version;
- score;
- variable contract;
- latency;
- error status.

### Inventory log

- candidate depth;
- coverage;
- snapshot age;
- lower/upper;
- confidence;
- respaldo;
- reason codes;
- latency.

### Orchestrator log

- Quality;
- Inventory;
- Opportunity;
- final action;
- capacity/rank context;
- policy version.

Usar correlation id para seguir:

event → Quality → Inventory → Opportunity → CRM.

---

## 16. Lineage checks

Automatizar:

- variable hash coincide con registry;
- schema version permitida;
- model version activa;
- calibrator correcto;
- snapshot_date <= decision_time;
- spot.created_at <= decision_time;
- candidate IDs reproducibles;
- config hash;
- recommendation count <= K.

Un lineage failure invalida la afirmación de reproducibilidad.

---

## 17. Taxonomía de cambio temporal

### Population cambio temporal

Cambió lead mix.

### Label cambio temporal

Cambió base rate/resultado generation.

### Process cambio temporal

Cambió acquisition/intermediario workflow.

### Inventory cambio temporal

Cambió catálogo, candidate depth o capacidad de atención.

### Instrumentation cambio temporal

Cambió Availability coverage/frequency.

### Model degradation

La relación score→resultado se deterioró.

AssessmentSol1 muestra un caso importante: Availability coverage y candidate depth cambiaron fuertemente mientras el core categorical mix permaneció relativamente estable.

---

## 18. Retraining triggers

Considerar retraining si, en varias cohortes maduras:

- Lift@10 deja de superar 1;
- calibration se degrada materialmente;
- score-resultado monotonicity se rompe;
- variable mix cambia persistentemente;
- base rate cambia y recalibration no basta.

No reentrenar automáticamente por:

- spike de un día;
- outage de Availability;
- candidate-depth cambio temporal;
- cambio Inventory que no toca Quality inputs.

---

## 19. Recalibration vs retraining

Si el ordenamiento sigue funcionando pero Brier/observed-vs-predicted empeoran, puede bastar recalibrar.

Si Lift/order deterioran, se requiere reevaluar el modelo.

Model y calibrator deben ser versiones distintas.

---

## 20. Champion/alternativa evaluada

alternativas evaluadas futuros:

- nueva Logistic;
- CatBoost;
- T2;
- Actionability Gate;
- Inventory V2 probabilística.

Reglas:

1. mismo contrato;
2. misma población;
3. mismas temporal folds;
4. no usar muestra de evaluación consumido para selección;
5. proper scoring + Lift;
6. shadow antes de promoción.

Una métrica aislada mejor no basta.

---

## 21. reversión guía operativa

### Caso A — Quality corrupto

Síntomas:

- scores constantes inesperados;
- NaNs;
- schema failure;
- fingerprint no esperado.

Acción:

1. congelar promoción;
2. pin last-known-good;
3. workflow estándar;
4. reprocesar eventos afectados cuando sea seguro.

### Caso B — Availability atrasada

1. mantener último estado conocido;
2. marcar vigencia;
3. Uncertain si excede política;
4. verificar inventario;
5. no declarar UNAVAILABLE por missing.

### Caso C — Inventory service caída

1. persistir Quality;
2. no calcular Opportunity falso;
3. marcar INVENTORY_TECHNICAL_UNAVAILABLE;
4. workflow estándar/verify;
5. retry idempotente.

### Caso D — Candidate logic violation

Si aparece future Spot, future snapshot o known unavailable recomendado:

**circuit-breaker de Inventory**.

No degradar silenciosamente.

### Caso E — Opportunity Orchestrator caído

Quality e Inventory pueden mostrarse por separado. No inventar product score.

### Caso F — CRM caído

Persistir decision record y reintentar el adapter. No recalcular un score distinto innecesariamente.

---

## 22. NO_RESULT vs error técnico

### NO_RESULT

La política funcionó correctamente y no encontró candidato válido.

### TECHNICAL_ERROR

La política no pudo ejecutarse correctamente.

Mezclarlos hace que Coverage@K y capacidad de atención sean ininterpretables.

---

## 23. A/B monitoring

Codexway propone:

- unidad lead_id;
- 50/50 sticky;
- ITT;
- SRM;
- pre-treatment eligibility;
- maturity/censoring.

### ordenamiento pilot

Primary:

scheduled_visit within 30 days.

Guardrails:

- time to first contact;
- contact attempts;
- intermediario workload;
- opt-out.

### respaldo pilot

Primary:

accepted alternative or scheduled visit within 30 days.

Guardrails:

- recommendation latency;
- no-result;
- distance relaxation;
- complaint rate.

---

## 24. Panel mínimo

### Sistema

- requests;
- success/error;
- p50/p95/p99 latency;
- queue volume;
- versions.

### Quality

- base rate;
- score distribution;
- Lift@K;
- recall;
- calibration;
- cambio temporal.

### Inventory

- Availability coverage;
- snapshot age;
- candidate depth;
- capacidad de atención;
- uncertainty;
- Coverage@K;
- NO_RESULT.

### Opportunity

- lower/upper;
- top-K overlap vs Quality;
- capacidad de atención entre priority;
- conversion guardrail;
- joint resultado cuando exista.

---

## 25. Promotion gate

Antes de shadow → acción:

### Data

- schema OK;
- lineage OK;
- cero future violations;
- vigencia aceptable.

### Quality

- PR-AUC > prevalence;
- Lift@10 >1;
- temporal persistence;
- calibration sin degradación material.

### Inventory

- constraints correctas;
- known-unavailable recommendations = 0;
- coverage/vigencia operacionalmente aceptables.

### Opportunity

- objetivo declarado;
- absolute Lift >1 si se usa para ordenamiento;
- trade-off vs Quality aceptado explícitamente;
- sin claim de probabilidad conjunta.

### Experiment

- SRM pass;
- maturity complete;
- guardrails pass.

---

## 26. Gobierno de cambios

Toda promoción registra:

- motivo;
- evidencia;
- owner;
- approver;
- versión anterior;
- versión nueva;
- diff de variables/config;
- metrics;
- reversión variable objetivo;
- activation date.

Cambios de variable objetivo o momento de evaluación crean un nuevo contrato, no una minor version silenciosa.

---

## 27. Resumen

| Área | Qué vigilar |
|---|---|
| Calidad del lead | base rate, score distribution, Lift@K, calibration, variable cambio temporal |
| Inventory | Availability coverage, snapshot age, candidate depth, capacidad de atención |
| respaldo | Coverage@K, UNKNOWN/VERIFY, NO_RESULT, violations |
| Opportunity | lower/upper, delta vs Quality, conversion vs serviceable objective |
| Plataforma | latency, errors, lineage, artifact versions |
| Experimento | SRM, ITT, maturity, guardrails |
| Gobierno | registry, retraining, approval, reversión |

El sistema sólo está sano cuando Quality, Inventory y Opportunity siguen siendo interpretables simultáneamente.
