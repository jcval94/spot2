# Cronología — Segmentación, perfiles y Matching

Esta cronología conserva cómo cambió la recomendación; no reescribe la historia como si Dynamic Need o Broker Service hubieran sido obvios desde el inicio.

## 1. Punto de partida: clustering como forma de explicar entidades

La línea comenzó buscando arquetipos de Lead, Spot y Broker que negocio pudiera entender y usar para matching.

Los primeros resultados mostraron perfiles interpretables, pero también riesgo de clusters dominantes, leakage histórico y mezcla de conceptos. Esto motivó `profile_clustering_v2`.

## 2. Profile Clustering v2: balance + point-in-time

`experimentos/profile_clustering_v2/`

Se probaron K-Means, Bisecting K-Means, BIRCH y Gaussian Mixture, K=3..7. La selección no usó target y penalizó desbalance. Se congelaron calibration, predictive train y future test.

Hallazgos:

- Persona P1–P7: dominada por `source` e historia;
- Search Need N1–N3: limpio;
- Spot S1–S7: mezcla geografía y físico;
- Inquiry Intent I1–I7: casi weekday;
- Broker: interpretable, pero velocidad de respuesta con semántica dudosa.

**Decisión provisional:** clustering sirve para entender estructura; más facetas no implican mejor ranking.

Evidencia: EV-006 / D006, D009–D012.

## 3. La pregunta cambia: cruzar las tablas, no analizarlas aisladas

El usuario pidió revisar relaciones y completar un A/B offline. Se abrió `experimentos/matching_ab_v3/` y primero se auditó PK/FK, cardinalidades, Lead→Inquiry→Spot, Availability, presupuestos, Market Context, response hours y agregados Spot.

Hallazgos que cambian el diseño:

- Inquiry×Availability por `spot_id` explota ~10.02x;
- Availability debe ser backward-as-of;
- modality actúa como hard constraint;
- sector/municipio/corredor son preferencias blandas;
- Inquiry refina presupuesto y área;
- response_hours no es SLA limpio;
- total_inquiries no reconcilia con events;
- Market Context no tiene coverage/effective time suficiente;
- Availability tiene coverage drift temporal.

Evidencia: EV-010 / D025–D033.

## 4. E006 matching_ab_v3: Physical vs Location

Control: Spot unificado.  
Tratamiento: Physical Space + Location.

Se construyeron PH1–PH4 y LOC1–LOC7.

La semántica mejoró claramente, pero ΔAP quedó prácticamente en cero con IC95% cruzando cero.

**Decisión:** conservar Physical + Location por calidad conceptual, no por lift demostrado.

Evidencia: EV-010 / D023.

## 5. E007 matching_ab_v3: flat compatibility

Se añadieron interacciones Persona×Need, Need×Physical, Need×Location, Need×Broker, Physical×Broker y Need×Physical×Broker.

Resultado:

- AP y métricas lead-level suben en punto;
- bootstrap inquiry-level no demuestra diferencia robusta;
- aparecen pockets de hasta ~1.366x lift suavizado.

**Decisión:** E007 queda como referencia global y las celdas como hipótesis, no uplift causal.

Se pre-registró A/B online sticky por Lead y power analysis.

Evidencia: EV-010 / D024, D032.

## 6. Revisión antes de cerrar: cuatro pendientes

Se detectaron cuatro preguntas:

1. Persona seguía mezclando canal y madurez;
2. Search Need debía actualizarse T0→T1;
3. Broker debía reconstruirse sin response_hours;
4. compatibilidad parecía jerárquica.

Esto abrió `experimentos/matching_profiles_v4/`.

## 7. E008: Behavioral Persona

Se separó `source` de BP1–BP3.

Semánticamente quedó mejor:

- BP1 baja historia;
- BP2 manufacturing/baja historia;
- BP3 alta madurez.

Pero AP y Lift@10 empeoraron.

**Decisión:** BP queda como explicación; no reemplaza Persona actual en scoring.

Evidencia: EV-013 / D038.

## 8. E009: Dynamic Need T1

Se construyó DN1–DN5 con requested area/budgets, urgency, asked_visit, channel, message length y deltas contra Need T0. Weekday quedó excluido.

Aparece **DN4 — stretch-space**: mucho más espacio solicitado con presupuesto relativamente bajo.

La primera rama recuperó lift, pero heredaba el deterioro de E008.

**Decisión:** aislar Dynamic Need contra el baseline fuerte.

Evidencia: EV-013 / D039.

## 9. E010/E011: primer Broker clean + jerarquía

Broker se separó en Supply y Service, sin response_hours.

Broker Supply v1 colapsó 98.3% de brokers en un cluster. E011 jerárquico mejoró algunos puntos lead-level, pero no superó E007 globalmente.

**Decisión:** volver al baseline fuerte y probar cambios uno por uno.

Evidencia: EV-013 / D040–D041.

## 10. Incidencia de reproducibilidad: primera corrida v4

Run `33286801380`.

El cálculo científico terminó, pero el harness falló porque el generador no escribió el filename exacto esperado para algunos experiment IDs, por ejemplo `E009_dynamic_need_t1_results.json`.

Se alinearon spec ID, model key, result filename y `results.experiment_id` sin cambiar hipótesis ni población.

## 11. E012: Dynamic Need sobre el baseline fuerte

Se volvió a E006 y se añadió sólo Dynamic Need + Need transition.

Resultado:

- AP sube ligeramente;
- Lift@10 pasa a **1.108x**;
- Recall@20 sube a **21.96%**;
- AP no se separa robustamente por bootstrap.

**Decisión:** Dynamic Need queda como challenger T1 y faceta de routing.

Evidencia: EV-013 / D042.

## 12. E013: segundo intento de Broker Supply con gate duro

Se probaron variables compactas, dominant specialization, entropías, log transforms y winsorization.

Gate:
- min cluster >=5%;
- max cluster <=65%.

Resultado:
- 70.3% / 26.0% / 3.7%;
- ARI 0.949;
- FAIL.

Run `33287041844` se detuvo deliberadamente.

**Decisión:** Broker Supply no debe forzarse a clustering. E013/E014 quedan no elegibles.

Evidencia: EV-013 / D043–D044.

## 13. Pivot: Broker Service sí pasa

### E015

BSV1–BSV3:

- balanceados;
- ARI 0.948;
- sin response_hours.

Como feature marginal, AP casi no cambia.

**Decisión:** BSV queda como faceta auxiliar, no driver global demostrado.

Evidencia: EV-013 / D045.

## 14. E016: Dynamic Need × Spot × Broker Service

La jerarquía sobre la rama válida eleva Lift@10 en punto y mejora algunas métricas lead-level, pero pierde AUC/recall y no supera robustamente E007 en AP.

**Decisión:** no existe nuevo ganador universal.

Evidencia: EV-013 / D046, D049.

## 15. Mejor pocket encontrado

**DN4 × LOC1 × BSV1**

- N=60;
- raw 36.67%;
- smoothed 31.37%;
- lift **1.510x**.

También se observa que N1/renta permanece casi siempre DN1, mientras N2/N3 se fragmentan y ganan más resolución en T1.

**Decisión:** priorizar esta familia en nueva evidencia, no convertirla en regla.

Evidencia: EV-013 / D047–D048.

## 16. Cierre

Runs autoritativos:

- profile clustering v2 `33278286046`;
- matching A/B v3 `33281634395`;
- matching profiles v4 `33287168139`;
- v4 rerun reproducible final `33287533072`;
- governance final `33287533051`.

La línea se cierra porque las alternativas plausibles ya fueron probadas, los negativos están preservados y seguir descubriendo pockets en el mismo test dejaría de ser confirmatorio.

El siguiente paso válido para DN4×LOC1×BSV1 es **nueva cohorte o A/B online**.
