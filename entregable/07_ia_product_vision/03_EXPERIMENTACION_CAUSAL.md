# Diseño causal — medir impacto incremental

## 1. Por qué hace falta un experimento online

El backtest responde:

> ¿el score ordena históricamente outcomes?

No responde:

> ¿usar el score cambia el outcome?

La priorización altera:

- qué lead recibe atención;
- cuándo;
- qué Spot se muestra;
- broker workload;
- inventory competition.

Eso requiere causalidad.

---

## 2. Separar mecanismos

Recomiendo no probar todo en un solo treatment inicialmente.

Dos experimentos permiten identificar valor incremental con mayor claridad.

### Experimento A — Opportunity-aware prioritization

Pregunta:

> ¿Trabajar leads con el ranking propuesto mejora outcomes frente al ordering actual?

### Experimento B — Contextual fallback

Pregunta:

> Cuando el Spot exacto no es servible, ¿mostrar el fallback gobernado mejora aceptación/visita frente al proceso actual?

Separarlos evita no saber si un efecto proviene del ranking o de la recomendación.

---

# Experimento A — Ranking

## 3. Población

Leads elegibles en T1:

- primera inquiry persistida;
- schema válido;
- Lead Quality producido;
- Inventory evaluable o explicitamente Uncertain;
- no exclusión por policy.

Eligibility debe definirse **antes** de asignación.

---

## 4. Unidad de randomización

Primaria:

**lead_id**.

Asignación:

**50/50 sticky**.

Un lead nunca cambia de arm durante la ventana experimental.

Esta decisión coincide con el protocolo emitido por Codexway.

---

## 5. Estratificación

Como mínimo:

- search_sector;
- source;
- calendar_week.

Opcional, si volumen lo permite:

- modality;
- geography macro;
- broker pool.

No crear demasiados strata pequeños.

---

## 6. Control

**Ordering operacional actual.**

No utilizar retrospectivamente un baseline simulado.

El control debe representar lo que realmente recibiría el lead sin el producto nuevo.

---

## 7. Tratamiento

Usar la política de ranking previamente congelada.

La UI muestra:

- Quality;
- Inventory;
- Opportunity;
- reason/action.

No cambiar fórmula ni threshold durante el experimento.

---

## 8. Primary KPI

Para la primera prueba recomiendo mantener el KPI preregistrado de Codexway:

**lead-level scheduled_visit within 30 days of first eligible exposure.**

Razón:

- observable;
- ya existe como proxy histórico;
- permite comprobar que la nueva priorización no destruye la señal comercial.

---

## 9. Key secondary KPI alineado a Product Vision

Con la nueva instrumentación:

**serviceable scheduled visit within 30 days.**

Definición:

- visita agendada;
- Spot exacto o alternativa aceptada bajo inventario válido en el momento de la recomendación.

Este KPI debe predefinirse antes de leer resultados.

---

## 10. Secondary outcomes

- accepted_or_scheduled;
- completed visit;
- time to first qualified response;
- alternative acceptance;
- deal opened;
- closed won;
- commercial value.

La multiplicidad debe corregirse o declararse exploratoria.

---

## 11. Guardrails

### Operación

- time to first contact;
- contact attempts;
- broker workload;
- queue starvation.

### Inventory

- Availability as-of coverage;
- snapshot age;
- unavailable recommendation rate;
- NO_RESULT;
- fallback Coverage@K.

### Customer

- opt-out;
- complaint rate;
- repeated irrelevant recommendations.

### Technical

- scoring latency;
- error rate;
- missing score;
- stale snapshot rate.

---

## 12. Sample-ratio mismatch

Ejecutar diariamente:

- global;
- por strata principales.

Verificar que treatment share ≈50%.

Codexway ya implementa un helper determinístico de assignment y un estadístico de SRM.

Un SRM material es un blocker de inferencia causal hasta explicar el problema.

No corregirlo simplemente reponderando después si proviene de un bug de assignment/exposure.

---

## 13. Intention-to-treat

Análisis principal:

**ITT por lead asignado.**

Un lead asignado a treatment cuenta como treatment aunque:

- el broker no vea la tarjeta;
- no use el fallback;
- ignore el ranking.

Esto estima el efecto del producto real, incluida adopción imperfecta.

Per-protocol puede reportarse sólo como análisis secundario no causal puro.

---

## 14. Interference

El supuesto SUTVA puede fallar.

### Posibles spillovers

- brokers comparten capacidad;
- treatment puede consumir más atención;
- leads compiten por el mismo inventory;
- un Spot mostrado a un tratamiento deja de estar disponible para control;
- learning del broker puede cambiar su comportamiento con controles.

### Mitigación inicial

- sticky assignment;
- medir workload por arm;
- limitar proporción de tratamiento durante ramp;
- instrumentar inventory contention;
- separar listas/slots de atención si es operacionalmente posible.

### Si interference es material

Cambiar la unidad de randomización a cluster:

- broker × week;
- broker team × week;
- market/municipality × week.

La inferencia debe usar errores cluster-robust.

---

## 15. Ramp-up

Propuesta:

### Safety phase

5% treatment.

Objetivo:

- schema;
- latency;
- SRM;
- no future snapshots;
- no invalid recommendations.

### Early ramp

25% treatment.

Revisar:

- broker workload;
- no-result;
- customer guardrails.

### Main experiment

50/50.

El período de main analysis se preregistra.

No usar resultados de la safety phase para tuning del treatment que luego se evalúa en la misma ventana.

---

## 16. Duración

La duración no debe escogerse como “dos semanas” arbitrarias.

Debe cumplir:

1. tamaño de muestra requerido;
2. mínimo cuatro semanas de exposición para capturar ciclos semanales;
3. horizonte de outcome de 30 días;
4. tiempo adicional para label finality/data QA.

Codexway calcula de forma ilustrativa:

- baseline first-inquiry proxy ≈21.22%;
- relative MDE 10%;
- alpha 0.05;
- power 80%;
- aproximadamente **6,038 leads por arm**.

Ese número debe recalcularse con el baseline real del piloto.

Duración:

    max(4 semanas, N_total_requerido / eligible_leads_per_day)
    + 30 días de madurez
    + ventana de cierre de datos

No declarar una fecha final antes de conocer tráfico elegible real.

---

## 17. No peeking

No terminar el test porque el p-value cruzó 0.05.

Opciones válidas:

- fixed-horizon;
- diseño secuencial formal preregistrado.

La opción simple para este assessment:

**fixed horizon + no optional stopping.**

---

## 18. Segment analysis

Predefinir pocos segmentos:

- sector;
- modality;
- source;
- Quality band;
- Inventory band.

El primary result es global.

Los segmentos son:

- heterogeneity analysis;
- hypothesis generation.

No promover una nueva regla porque un subgrupo pequeño tenga p<0.05 sin corrección/madurez.

---

# Experimento B — Fallback

## 19. Población

Sólo leads donde el Spot exacto:

- no es attendable;
- es Uncertain y requiere alternativa;
- o cumple el trigger de fallback predefinido.

---

## 20. Unidad

**lead_id sticky**.

Control:

- proceso actual de búsqueda/alternativas.

Tratamiento:

- fallback rankeado point-in-time del Entregable 4.

---

## 21. Primary KPI

Codexway propone:

**accepted alternative or scheduled visit within 30 days.**

Con mejor instrumentación, idealmente separar:

- accepted alternative;
- scheduled visit;
- completed visit.

---

## 22. Guardrails del fallback

- recommendation latency;
- NO_RESULT;
- distance/geographic relaxation;
- known-unavailable recommendation rate;
- complaint rate;
- broker workload;
- repeated suggestion rate.

Hard guardrail:

**known unavailable recommendation rate = 0.**

---

## 23. Gold de recomendación online

El RCT genera por fin el dato que falta en offline:

- qué candidato se mostró;
- en qué rank;
- qué arm;
- qué aceptó el usuario;
- qué visitó;
- qué cerró.

Esto permite evaluar después:

- Hit@K real;
- MRR/NDCG si tiene sentido;
- acceptance@K;
- value@K;
- contextual ranking.

El historical chosen Spot deja de ser el pseudo-gold.

---

# Experimentación del LLM / Catalog QA

## 24. Diseño humano

Antes de cualquier automatic gate:

1. sample ciego;
2. dos revisores si es viable;
3. adjudicación;
4. gold freeze;
5. después revelar Rules/LLM outputs.

Primary metrics:

- precision humana;
- recall;
- actionable precision;
- novelty;
- review burden;
- cost por issue validado.

No usar otro LLM como gold.

---

# Quasi-experimental fallback si RCT no es viable

## 25. Alternativa principal — phased rollout + Difference-in-Differences

Si la organización no permite randomización individual:

### Diseño

- seleccionar mercados/equipos comparables;
- introducir producto en cohortes escalonadas;
- conservar grupos aún no tratados;
- medir múltiples períodos pre y post.

### Análisis

- Difference-in-Differences;
- event-study;
- cluster-robust SE;
- controles por calendario/mercado;
- pre-trend tests.

### Requisito

La fecha de rollout no debe elegirse según performance reciente del mercado.

---

## 26. Alternativa secundaria — Regression Discontinuity

Si existe un cutoff de capacidad rígido y no manipulable:

- comparar leads justo arriba y abajo del cutoff;
- estimar efecto local de recibir prioridad.

Limitaciones:

- sólo efecto local;
- ties/ranking pueden complicar continuidad;
- inventory spillovers pueden violar supuestos.

No es preferible al RCT.

---

## 27. Switchback para interference fuerte

Si el problema principal es capacidad compartida de broker/inventory:

Randomizar períodos:

- team-day;
- broker-day;
- market-day/week.

Alternar control/treatment.

Ventajas:

- reduce contaminación dentro del mismo recurso compartido.

Riesgos:

- carryover;
- seasonality;
- learning.

Requiere washout/period design.

---

## 28. Criterio de decisión

No promover por “significancia” solamente.

La decisión debe considerar:

- effect size;
- CI;
- primary KPI;
- conversion guardrail;
- serviceability gain;
- broker workload;
- customer guardrails;
- operational cost;
- stability por cohortes.

---

## 29. Registro experimental

Antes de launch congelar:

- hypothesis;
- treatment;
- eligibility;
- randomization;
- strata;
- primary KPI;
- secondary metrics;
- guardrails;
- MDE;
- power;
- sample size;
- duration rule;
- exclusion rules;
- analysis plan;
- stopping rule.

Después del launch no cambiar definiciones sin declarar una nueva versión.

---

## 30. Resultado causal que buscamos

La pregunta final no es:

> ¿el score tiene mejor AUC?

Es:

> **¿usar esta política provoca más outcomes comerciales útiles por lead elegible, sin deteriorar experiencia, inventory quality ni workload?**

Ésa es la prueba que el offline no puede resolver.
