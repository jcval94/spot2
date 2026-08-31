# Entregable 5 — Puntaje de oportunidad

> ### Lectura en lenguaje claro
> **En una frase:** el Puntaje de oportunidad combina qué tan prometedor es el lead con qué tan posible es atenderlo, pero mantiene ambas señales visibles porque responden a objetivos de negocio distintos.
>
> Algunos nombres técnicos se conservan porque corresponden a métricas o variables reproducibles. **Lift@10** compara el 10% mejor priorizado contra elegir al azar el mismo número de casos; **variable objetivo** es el resultado que se quiere anticipar; **disponible en ese momento / as-of** significa usar sólo información que ya era conocida en ese momento; **muestra de evaluación** es una muestra apartada para evaluación; y **respaldo** es la estrategia de respaldo cuando la opción original no puede recomendarse con suficiente confianza.
>

## 1. Propósito

El Puntaje de oportunidad integra dos señales que responden preguntas diferentes:

- **Calidad del lead:** probabilidad calibrada de que la primera consulta termine en `scheduled_visit`.
- **Capacidad del inventario:** capacidad del inventario disponible en ese momento de atender razonablemente la necesidad del lead.

No se reentrena ni rediseña ninguno de los dos componentes.

El objetivo del Puntaje de oportunidad es construir una capa de decisión operativa que responda:

> ¿Qué leads combinan suficiente probabilidad de progresar con suficiente capacidad real de servicio?

---

## 2. Arquitectura final de Codexway

La implementación canónica está en:

- `codexway/src/spot2_codexway/inventory.py::combine_opportunity`;
- `codexway/outputs/metrics/system_evaluation.json`;
- `codexway/outputs/metrics/system_score_*`;
- `codexway/evidence/EV-114_OPPORTUNITY_LIFT.md`.

La fórmula final es:

```text
Lead Quality Score = 100 × p_lead_quality

Opportunity probability lower
  = p_lead_quality × inventory_serviceability_lower

Opportunity probability upper
  = p_lead_quality × inventory_serviceability_upper

Opportunity Score = 100 × Opportunity probability lower
```

La salida lower es la vista conservadora y es la que gobierna el score principal. La upper conserva el potencial cuando Inventory es UNKNOWN/stale.

### Por qué existen lower y upper

Inventory no siempre está perfectamente observado.

Cuando Availability es desconocida o stale, Codexway no impone:

`UNKNOWN = UNAVAILABLE`.

En lugar de eso, el componente de Inventory puede tener una cota inferior conservadora y una cota superior optimista. El Puntaje de oportunidad hereda esa incertidumbre.

Esto evita dos errores:

1. afirmar servicio inexistente cuando sólo faltan datos;
2. inflar el ordenamiento usando como segura una disponibilidad no confirmada.

---

## 3. Qué significa —y qué no significa— el score

### Sí significa

Un **score de priorización operacional** que combina:

- señal comercial T1;
- posibilidad de atender al lead con inventario conocido al score;
- incertidumbre explícita.

### No significa

- probabilidad causal de venta;
- probabilidad conjunta perfectamente calibrada;
- probabilidad de éxito del respaldo;
- garantía de que el Spot será aceptado;
- sustituto de Calidad del lead para cualquier objetivo;
- evidencia de valor causal de Inventory.

El variable objetivo observado de Codexway es `scheduled_visit` en la primera consulta. Ese variable objetivo **no observa aceptación de un respaldo recomendado**, por lo que el valor incremental de Inventory no puede validarse de forma limpia contra ese resultado.

---

## 4. Dos objetivos de negocio distintos

### Objetivo A — Maximizar progresión/conversión proxy

Pregunta:

> Con capacidad limitada, ¿qué leads concentran más `scheduled_visit`?

Señal correcta:

`Lead Quality`.

### Objetivo B — Maximizar oportunidades además serviceable

Pregunta:

> ¿Qué leads tienen señal comercial y además inventario defendible para ser atendidos?

Señal correcta:

`Lead Quality + Inventory Serviceability + Opportunity Score`.

No debe evaluarse el segundo objetivo sólo con el variable objetivo del primero.

---

## 5. Trade-off observado

En el muestra histórica de evaluación común de Codexway:

| Score | ROC-AUC | PR-AUC | Brier | Lift@5 | Lift@10 | Recall@10 |
|---|---:|---:|---:|---:|---:|---:|
| Calidad del lead | 0.5478 | 0.2391 | **0.1658** | **1.689x** | **1.689x** | **16.98%** |
| Opportunity lower | 0.5119 | **0.2477** | 0.1707 | 1.589x | 1.370x | 13.77% |
| Opportunity upper | 0.5235 | 0.2613 | 0.1695 | 1.809x | 1.507x | 15.15% |

La comparación pareada Quality → Opportunity lower muestra:

- ΔROC-AUC = **-0.0359**, IC95% [-0.0696, -0.0011];
- ΔLift@10 = **-0.3186x**, IC95% [-0.6252, -0.0125];
- ΔRecall@10 = **-3.20 pp**, IC95% [-6.28, -0.13 pp];
- ΔBrier = **+0.00494**, peor para el variable objetivo T1;
- ΔPR-AUC = +0.0086, con intervalo que cruza cero.

### Interpretación

El Puntaje de oportunidad conservador:

- **sí** supera random de forma absoluta: Lift@10 1.370x, IC95% [1.078x, 1.690x];
- **no** demuestra valor incremental sobre Calidad del lead para ordenar el variable objetivo T1;
- reduce la concentración de `scheduled_visit` cuando penaliza leads con inventario menos servible.

Esto no es una contradicción: refleja que **conversión proxy y capacidad de atención son objetivos diferentes**.

---

## 6. Política de dos ejes

Codexway no recomienda esconder todo dentro de un único ordenamiento.

La política diagnóstica del sistema distingue:

| Calidad del lead | Inventory | Acción |
|---|---|---|
| Alta/Priority | Serviceable | trabajar si el gate del modelo está activo |
| Alta/Priority | Uncertain | verificar inventario primero |
| Alta/Priority | baja capacidad de atención | buscar/ofrecer respaldo |
| Standard | cualquiera | workflow estándar |

El código define la banda de Inventory como:

- **Uncertain:** `inventory_confidence < 0.50` o `uncertainty_width > 0.20`;
- **Serviceable:** lower >= 0.75;
- **Potential respaldo:** upper >= 0.50;
- **Low capacidad de atención:** resto.

Esta vista de dos ejes debe permanecer visible aun cuando se use Puntaje de oportunidad.

---

## Alternativas arquitectónicas evaluadas

### 7.1 Quality-only

```text
Priority = p_lead_quality
```

**Tiene sentido cuando:**
- el objetivo primario es maximizar el variable objetivo T1;
- Inventory no limita la capacidad operativa;
- el intermediario puede resolver inventario después;
- se quiere la mejor concentración comercial observada.

**Ventaja:** es la señal que mejor ordena `scheduled_visit` bajo Codexway.

**Limitación:** puede priorizar leads que hoy no tienen un Spot defendible.

---

### 7.2 Quality × Inventory — producto continuo simple

```text
p_quality × inventory_serviceability
```

**Tiene sentido cuando:**
- Calidad del lead es verdaderamente independiente de señales de Spot/Inventory;
- Inventory tiene escala interpretable;
- el objetivo exige castigar gradualmente la baja capacidad de atención.

**Riesgos:**
- una señal de inventario mal calibrada puede dominar el ordenamiento;
- si Quality ya incorporó matching, puede haber double counting;
- un punto estimado oculta incertidumbre.

---

### 7.3 Quality × InventoryActionabilityGate

Arquitectura de AssessmentSol1 V2:

```text
p_quality × inventory_actionability_gate
```

El gate evita multiplicar de nuevo una señal continua de matching.

**Tiene sentido cuando:**
- el modelo de Calidad del lead ya incluye selected-Spot matching o contexto de capacidad de atención;
- volver a multiplicar Inventory introduciría solapamiento;
- se quiere que Inventory actúe como elegibilidad/abstención más que como segundo scorer.

AssessmentSol1 llegó a esta arquitectura porque su Calidad del lead recuperado utiliza:

- `selected_spot_area_closeness`;
- `selected_spot_geographic_fit`;
- `selected_spot_attribute_completeness`.

En esa arquitectura, multiplicar `InventoryServiceability` de nuevo podía double-count matching.

**No se promueve aquí**, porque ese no es el Calidad del lead canónico de Codexway.

---

### 7.4 Arquitectura final de Codexway — producto continuo con incertidumbre + dos ejes

Codexway utiliza:

```text
p_quality × inventory_serviceability_lower
```

y conserva en paralelo:

```text
p_quality
inventory_serviceability_lower
inventory_serviceability_upper
inventory_confidence
inventory_uncertainty_width
fallback
```

**Por qué no es equivalente al producto simple:**

1. usa lower/upper bounds;
2. trata UNKNOWN/stale como incertidumbre;
3. mantiene los componentes visibles;
4. define acciones diferentes para Inventory incierto;
5. no afirma una probabilidad conjunta calibrada;
6. no autoriza despliegue por el solo hecho de que el producto sea >0.

**Por qué no hay double counting estructural en Codexway:**

El Calidad del lead final de Codexway es `stable_segment_logistic` con la interacción T0-safe:

`Industrial AND (company_size=small OR source=paid)`.

No utiliza Availability ni selected-Spot capacidad de atención. Inventory permanece en un componente separado. Por eso la razón que llevó a AssessmentSol1 a un Actionability Gate **no aplica automáticamente** a la arquitectura canónica.

---

## 8. Evidencia histórica incompatible y cómo usarla

### E020 — P_quality × P_inventory_top3

E020, bajo otro modelo y otro contrato experimental, reportó mejoras sobre un proxy conjunto:

- macro Lift@10 Quality-only: 1.312x;
- macro Lift@10 Opportunity: 1.450x;
- fold final P85: 106 → 114 joint positives;
- +7.5% de joint positives;
- pero conversion positives: 124 → 114, delta **-10**.

Es un robustness check valioso porque exhibe el mismo trade-off:

> mejorar concentración de oportunidades atendibles puede reducir conversión pura.

No se copian sus métricas como performance de Codexway.

### AssessmentSol1 V2 — Actionability Gate

Es evidencia metodológica de que una arquitectura debe revisarse cuando cambia el contenido del Calidad del lead.

No invalida Codexway; explica cuándo un producto continuo **sí** podría ser double counting.

---

## Sensitivity analysis y nomenclatura V1/V2

Las etiquetas “V1” y “V2” no son globales al repositorio.

### Línea histórica E020

La arquitectura histórica fue un producto continuo entre Quality y una probabilidad de Inventory top-3. Es evidencia de integración, no la autoridad final de Codexway.

### AssessmentSol1

En esa rama:

- Opportunity V1 = producto continuo Quality × Capacidad del inventario;
- Opportunity V2 = Quality × InventoryActionabilityGate.

V1 fue rechazado allí por double counting después de que su Calidad del lead recuperado incorporara selected-Spot matching.

### Codexway

Codexway no hereda automáticamente esa invalidación porque su Calidad del lead final no contiene Availability ni selected-Spot capacidad de atención. Su arquitectura final sigue siendo:

    p_quality × inventory_serviceability_lower

con upper bound, confidence y política de dos ejes.

### Sensibilidades relevantes

| Sensibilidad | Lectura |
|---|---|
| Opportunity lower | vista conservadora y score principal |
| Opportunity upper | potencial bajo incertidumbre de Inventory |
| Quality-only | benchmark para maximizar variable objetivo T1 |
| Capacity 5/10/20% | sensibilidad operacional congelada en Codexway |
| K interno top-3 | sensibilidad incorporada al componente de capacidad de atención |
| hasta K=5 visible | política final de respaldo de Codexway |
| Actionability Gate | alternativa evaluada sólo si Calidad del lead incorpora matching solapado |

La regla de interpretación es: **no trasladar el nombre V1/V2 entre ramas sin trasladar también el modelo de Calidad del lead, el contrato, la población y la política de Inventory que le dieron significado.**

---

## 9. Thresholds y capacidad

Codexway congela una política capacity-first:

- default: **top 10%**;
- escenarios: **5%, 10%, 20%**.

Para Calidad del lead, el threshold de prioridad derivado de validation es:

`p ≈ 0.2530980692`.

No es un cutoff universal de “buen lead”.

Para Opportunity, el código construye bandas con percentiles de validation:

- Low;
- Medium;
- High;
- Priority.

La práctica recomendada en operación es trabajar por **capacidad/rank** y no convertir un threshold histórico en regla eterna.

### Scores empatados

El modelo final tiene resolución baja y empates reales.

Evaluación:
- usar métricas tie-aware / expected fractional capture.

Operación:
- nunca depender del orden físico de filas;
- usar una política de desempate explícita, estable y auditable;
- si no existe criterio de negocio, utilizar hash aleatorio estable del lead dentro del bucket empatado.

---

## 10. T0, T1 y T2

### T1 — canónico

Es el scoring principal.

Trigger:

`first inquiry persisted → score before broker response`.

### T0 — sensibilidad/cold start

Codexway lo mantiene como sensibilidad de planificación.

Su señal es débil y el variable objetivo cambia con exposición futura. No debe sustituir T1 ni mezclarse con sus probabilidades.

**Producción:** no usar T0 como prioridad automática con la evidencia actual.

### T2 — alternativa evaluada de rescore

T2 usa consultas posteriores con historia estrictamente previa.

Puede ser útil como extensión dinámica, pero:

- estima otra pregunta;
- no debe mezclar sus scores con T1 sin calibración y política por stage;
- requiere promoción independiente.

**Producción inicial:** T1 solamente. T2 queda como futura extensión versionada.

---

## 11. Actualización dinámica

Hay que distinguir dos tipos de cambio.

### Cambia el lead / llega otra consulta

No sobrescribir el score T1.

- conservar score T1 original;
- si en el futuro se promueve T2, generar un nuevo `score_event` con stage=T2.

### Cambia Inventory

Calidad del lead T1 puede permanecer fijo, pero capacidad de atención puede cambiar.

Para una cola operacional viva se puede recalcular:

```text
p_quality_T1 fijo
×
inventory_serviceability_as_of(now)
```

Esto debe guardarse como **inventory refresh / operational rescore**, no como si hubiera sido el score histórico T1 original.

Así se conserva:

- auditabilidad;
- backtesting correcto;
- comparación entre “decisión original” y “estado actual”.

---

## 12. respaldo dentro de Opportunity

El respaldo ya está definido en el Entregable 4 y no se modifica.

Reglas relevantes:

- Availability strict backward-as-of;
- `UNKNOWN != UNAVAILABLE`;
- top-3 interno para componente de capacidad de atención;
- hasta K=5 recomendaciones visibles;
- `NO_RESULT` antes que violar hard constraints.

Opportunity consume el resultado de Inventory; no reconstruye candidatos por su cuenta.

---

## 13. Política operativa final

### Si el objetivo es conversión proxy

1. ordenar por Calidad del lead;
2. usar Inventory como contexto/guardrail;
3. no penalizar automáticamente Quality por Inventory salvo decisión de producto explícita.

### Si el objetivo es oportunidad serviceable

1. calcular Opportunity lower/upper;
2. priorizar por lower dentro de capacidad;
3. conservar Quality visible;
4. si Inventory es Uncertain, verificar antes;
5. si hay baja capacidad de atención, ofrecer respaldo;
6. si no hay candidato válido, permitir `NO_RESULT`.

### Activación

Estado de Codexway:

`ELIGIBLE_AFTER_NEW_FORWARD_SHADOW_VALIDATION`.

Secuencia:

1. nueva cohorte forward en shadow;
2. esperar madurez;
3. validar Quality y Opportunity por separado;
4. revisar cambio temporal/coverage/vigencia;
5. si persiste señal, piloto A/B sticky por `lead_id`;
6. análisis intention-to-treat.

---

## 14. Métricas que deben reportarse juntas

No basta con AUC.

### Quality

- base rate;
- PR-AUC;
- Brier / Log Loss;
- Lift@5/10/20;
- Recall@5/10/20;
- calibration;
- monthly stability.

### Inventory

- capacidad de atención lower/upper;
- confidence;
- uncertainty width;
- availability coverage;
- snapshot age;
- candidate depth;
- respaldo Coverage@K;
- UNKNOWN/stale;
- `NO_RESULT`.

### Opportunity

- distribución lower/upper;
- Lift@K sobre el objetivo declarado;
- recall/capture a capacidad;
- delta vs Quality;
- share de Priority con Inventory incierto;
- capacidad de atención entre leads priorizados;
- conversion guardrail;
- joint/serviceable resultados cuando exista un gold alineado.

---

## 15. Decisión final del Entregable 5

| Pregunta | Decisión |
|---|---|
| ¿Qué arquitectura manda? | Codexway |
| ¿Calidad del lead cambia? | No |
| ¿Inventory cambia? | No |
| ¿Fórmula final? | `p_quality × inventory_serviceability_lower` |
| ¿Se conserva upper bound? | Sí |
| ¿Es probabilidad conjunta calibrada? | No |
| ¿Inventory mejora el variable objetivo T1 vs Quality-only? | No demostrado; gate incremental NO-GO |
| ¿Opportunity supera random? | Sí, Lift@10 1.370x; IC95% >1 |
| ¿Uso inmediato automático? | No |
| ¿Siguiente paso? | Forward shadow + piloto guardado |
| ¿Actionability Gate final? | No; alternativa evaluada de AssessmentSol1 bajo otra arquitectura |
| ¿Objetivo de conversión pura? | Quality-only |
| ¿Objetivo serviceable? | Opportunity + dos ejes |
