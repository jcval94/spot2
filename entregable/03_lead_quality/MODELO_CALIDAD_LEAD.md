# Entregable 3 — Modelo de Calidad del Lead

> ### Lectura en lenguaje claro
> **En una frase:** el modelo no intenta predecir perfectamente quién convertirá; busca ordenar mejor los leads cuando el equipo tiene capacidad limitada, con una señal sencilla y defendible en el tiempo.
>
> Algunos nombres técnicos se conservan porque corresponden a métricas o variables reproducibles. **Lift@10** compara el 10% mejor priorizado contra elegir al azar el mismo número de casos; **target** es el resultado que se quiere anticipar; **point-in-time / as-of** significa usar sólo información que ya era conocida en ese momento; **holdout** es una muestra apartada para evaluación; y **fallback** es la estrategia de respaldo cuando la opción original no puede recomendarse con suficiente confianza.
>

## Resumen ejecutivo

El **Lead Quality Model** responde una pregunta muy concreta:

> **En el instante T1, inmediatamente después de persistir la primera inquiry y antes de conocer la respuesta del broker, ¿qué tan probable es que esa primera inquiry termine registrada como `scheduled_visit`?**

La solución final mantiene a **Codexway** como autoridad. El componente promovido es un modelo deliberadamente parsimonioso:

**`stable_segment_logistic` + calibración Platt**

Su única señal final es una interacción T0-safe y de baja cardinalidad:

`Industrial AND (company_size = small OR source = paid)`

Esta elección no surge de preferir simplicidad por principio. Surge de una investigación amplia en la que se probaron:

- reglas de negocio;
- regresiones logísticas con feature sets amplios;
- CatBoost;
- modelos especialistas por etapa;
- pooled models con stage;
- arquitecturas multi-head;
- trajectory/progression features;
- Dynamic Need;
- clustering y perfiles;
- semantic rules;
- features derivadas con LLM;
- selected-Spot matching;
- distintas estrategias de calibración y capacidad.

La conclusión final es que **la complejidad adicional no fue suficientemente estable o comparable para desplazar el contrato de Codexway**. El modelo final sacrifica separación global a cambio de una señal de ranking acotada, interpretable, temporalmente defendible y reproducible.

En el holdout procedimental de Codexway:

| Métrica | Resultado |
|---|---:|
| N | 1,711 |
| Prevalencia | 21.22% |
| ROC-AUC | 0.5478 |
| PR-AUC | 0.2391 |
| Brier | 0.1658 |
| Log Loss | 0.5129 |
| Precision@5% | 35.83% |
| Recall@5% | 8.49% |
| Lift@5% | **1.689x** |
| Precision@10% | 35.83% |
| Recall@10% | **16.98%** |
| Lift@10% | **1.689x** |
| Recall@20% | 26.80% |
| Lift@20% | 1.337x |

El Lift@10% tiene IC95% bootstrap **[1.381x, 1.982x]**.

La decisión operativa es **GO para nueva validación forward**, no autorización de automatización inmediata. El holdout histórico ya había sido consumido globalmente por investigación previa, por lo que el resultado final debe tratarse como evidencia retrospectiva y confirmarse en un nuevo periodo shadow antes de cualquier A/B productivo.

---

# 1. ¿Qué significa “Lead Quality”?

En este assessment, Lead Quality no significa “valor total del cliente”, “probabilidad de cierre”, “revenue esperado” ni “calidad absoluta”.

Significa:

> **probabilidad de progreso comercial temprano de una primera inquiry, medida mediante el proxy `scheduled_visit`.**

La variable de calidad está deliberadamente separada de **Inventory Serviceability**.

Esto evita confundir dos preguntas distintas:

1. **¿El lead parece proclive a avanzar?**
2. **¿Existe inventario históricamente observable y razonablemente atendible para ese lead?**

Un lead puede ser comercialmente atractivo y no contar con inventario atendible. También puede existir inventario adecuado para un lead de baja propensión.

Por eso Codexway no inserta Availability ni atributos de servicio del inventario dentro del predictor final de Lead Quality.

Fuentes:
- **Codexway README**
- **Model Card**
- **Decisiones congeladas**

---

# 2. Autoridad y jerarquía de evidencia

Este entregable utiliza tres capas de evidencia.

## 2.1 Autoridad final: Codexway

Codexway define:

- target;
- scoring moment;
- maturity;
- ABT;
- feature allowlist;
- modelo final;
- calibración;
- split temporal;
- política de tie handling;
- cutoff de prioridad;
- uso operativo.

Cuando una línea histórica llega a un modelo distinto, **no sustituye a Codexway** salvo bug metodológico verificable. No se encontró un bug que obligue a reemplazar su modelo final.

## 2.2 Evidencia complementaria: AssessmentSol1

AssessmentSol1 aporta principalmente:

- auditoría temporal;
- distinción event / observation / effective time;
- tratamiento de structural missingness;
- clean-room target semantics;
- pruebas de recovery;
- auditoría final de leakage;
- evidencia sobre T0/T1/T2 y selected-Spot context.

Sus resultados de Lead Quality no se presentan como leaderboard contra Codexway porque usa contratos diferentes, incluyendo otra madurez y otros artefactos de ABT.

## 2.3 Evidencia complementaria: experimentos

La carpeta `experimentos/` aporta:

- multi-head;
- especialistas;
- pooled CatBoost;
- rolling CV;
- trajectory;
- clustering;
- Dynamic Need;
- matching;
- semantic rules;
- LLM semantic feature pilot;
- resultados negativos y ablations.

Algunas de estas líneas usan snapshots, targets, poblaciones y ventanas diferentes. Sus métricas se reportan **dentro de cada familia de experimento**, no como si fueran directamente comparables con el modelo final.

---

# 3. Scoring moment: T1

## 3.1 Definición

La predicción principal se calcula en:

**T1 = primera inquiry del lead**

Grano:

`lead_id × first_inquiry`

Timestamp:

`min(inquiry_at)` por `lead_id`, usando `inquiry_id` ascendente como desempate determinista.

Instante operativo:

1. la inquiry actual ya fue persistida;
2. su payload ya es observable;
3. la respuesta del broker todavía no existe para el modelo.

## 3.2 Por qué T1 es el contrato principal

T0 tiene menos información y mezcla la calidad del lead con su futura exposición a generar inquiries.

T2 puede usar historia previa, pero sólo existe para leads que ya sobrevivieron hasta interacciones posteriores; por tanto, su población es condicional y no es directamente comparable con T1.

T1 es el mejor punto de equilibrio entre:

- utilidad operativa;
- señal contemporánea;
- suficiente cobertura;
- interpretación clara;
- control de leakage.

## 3.3 T0 y T2

Codexway conserva:

- **T0** como sensibilidad a 30 días;
- **T2** como challenger de re-scoring con historia estrictamente desplazada.

No se promedian T0, T1 y T2.

AssessmentSol1 llegó a la misma conclusión conceptual: T1 debe conservarse como contrato principal, aunque sus modelos concretos fueran distintos.

Fuentes:
- **Codexway README — Prediction timestamp**
- **Codexway targets.py**
- **AssessmentSol1 Stage Comparison**

---

# 4. Target, maturity y censoring

## 4.1 Target final de Codexway

El target T1 es positivo cuando:

`first_inquiry.broker_response == "scheduled_visit"`

Negativo cuando la primera inquiry madura tiene otra respuesta.

La variable es un **proxy de progreso comercial**.

No debe llamarse:

- cierre;
- venta;
- revenue;
- causal conversion;
- éxito del fallback.

## 4.2 Maturity

Codexway fija:

- data-as-of: **2026-07-01 00:00 UTC**;
- maturity buffer: **7 días**;
- cutoff de madurez: **2026-06-24**.

Una primera inquiry posterior al cutoff puede scorearse, pero no se usa todavía para evaluar el target.

Población:

- 4,898 leads maduros;
- 1,001 positivos;
- prevalencia: **20.44%**;
- 102 leads recientes con target NA pero scoreables.

## 4.3 Sensibilidades

Codexway también construye:

- maturity 14 días;
- maturity 30 días;
- `accepted_or_scheduled`;
- cualquier inquiry con scheduled visit iniciada dentro de 30 días.

Estas variantes se usan para sensibilidad, no para elegir post-hoc el target que produzca mayor AUC.

## 4.4 Evidencia clean-room

AssessmentSol1 usa un contrato más conservador con madurez de 14 días y explicita que un scheduled visit con tiempo de respuesta no reconstruible no debe reinterpretarse arbitrariamente.

Ese análisis complementario refuerza dos decisiones de Codexway:

1. no usar `broker_response_hours` como reloj confiable de label;
2. congelar target y maturity antes de optimizar modelos.

Fuentes:
- **Codexway README — Target**
- **Codexway base config**
- **AssessmentSol1 Target Contract**

---

# 5. Unidad de observación y ABT

## 5.1 Grain final

La ABT T1 tiene:

**una fila por lead en su primera inquiry**

con:

- `lead_id`;
- `inquiry_id` de la primera inquiry;
- `prediction_timestamp`;
- variables intake;
- payload de la inquiry actual;
- transforms determinísticos;
- target sólo para evaluación.

La función `first_inquiries()` ordena por:

`lead_id, inquiry_at, inquiry_id`

y valida que `lead_id` quede único.

## 5.2 Separación del inventario

Spot state y Availability no forman parte del Lead Quality final.

Se reservan para Inventory Serviceability y para el score combinado posterior.

Esto es importante porque AssessmentSol1 encontró señal de ranking al introducir selected-Spot matching. Sin embargo, también documentó que eso crea solapamiento conceptual con Inventory y obliga a revisar la combinación posterior.

Codexway evita ese doble conteo desde la arquitectura base.

---

# 6. Qué información es válida en T1

“Conocerse legalmente” se interpreta aquí en sentido metodológico: **ser observable y permitida por el contrato temporal en el instante de scoring**.

## 6.1 Permitido

La allowlist limpia de Codexway incluye:

### Intake del lead

- user_type;
- company_size;
- industry;
- search_sector;
- search_modality;
- target_area_sqm;
- budgets mínimos/máximos;
- preferred_state;
- preferred_municipality;
- preferred_corridor;
- source.

### Inquiry actual

- channel;
- message_length;
- requested_area_sqm;
- requested budgets;
- urgency_days;
- asked_visit.

### Derivadas contemporáneas

- days_from_lead_creation;
- area_request_to_target_ratio;
- rent_request_to_lead_budget_ratio;
- sale_request_to_lead_budget_ratio;
- industrial_small_or_paid_interaction.

## 6.2 Excluido por incertidumbre temporal

Codexway no promueve como clean features:

- prior_searches;
- prior_inquiries;
- has_converted_before.

El nombre de una columna no demuestra que el valor estuviera congelado históricamente en T1.

## 6.3 Prohibido

Se bloquean:

- `lead_score_internal`;
- `broker_response`;
- `broker_response_hours`;
- future inquiries;
- future scheduled outcomes;
- `days_on_market`;
- `total_inquiries`;
- `total_views`;
- `is_active`;
- `competing_inquiries_30d`;
- Market Context sin publication/effective time;
- texto/LLM sin versión histórica.

## 6.4 Availability

Availability sí puede ser históricamente reconstruida únicamente cuando:

`snapshot_date <= prediction_timestamp`

con backward as-of.

Aun así, se mantiene fuera del predictor de Lead Quality.

Fuentes:
- **Feature policy**
- **Features implementation**
- **Leakage Matrix**
- **AssessmentSol1 Temporal Semantics**

---

# 7. Structural missingness y preprocessing

AssessmentSol1 aporta un punto metodológico importante: **missing no siempre significa desconocido**.

Ejemplos:

- un presupuesto de venta puede ser no aplicable a una búsqueda sólo de renta;
- un presupuesto de renta puede ser no aplicable a una búsqueda sólo de venta;
- urgency faltante sí puede significar “no declarado”.

Por eso la investigación complementaria implementó estados de aplicabilidad y flags específicos.

Codexway, para los modelos logísticos amplios, aplica preprocessing dentro del pipeline:

- categóricas: `SimpleImputer(most_frequent)` + `OneHotEncoder(handle_unknown="ignore", min_frequency=5)`;
- numéricas: mediana + missing indicator;
- escalado numérico;
- transformación entrenada sólo con el fold/train correspondiente.

El modelo final promovido usa únicamente una interacción binaria, por lo que reduce radicalmente la dependencia de imputación, cardinalidad y drift de variables continuas.

---

# 8. Diseño temporal de validación

## 8.1 Split principal

Codexway congela:

| Partición | Intervalo first inquiry | N | Positive rate |
|---|---|---:|---:|
| Train | 2025-01-01 a 2025-09-23 | 2,191 | 20.22% |
| Validation | 2025-10-01 a 2025-12-23 | 847 | 19.48% |
| Holdout procedimental | 2026-01-01 a 2026-06-23 | 1,711 | 21.22% |

Entre particiones existe purge temporal de siete días.

## 8.2 Rolling temporal CV

La selección no depende sólo de un split único.

Codexway usa cuatro folds temporales para comparar familias y para evaluar el challenger de segmento estable.

Lift@10 del modelo estable por fold:

| Fold | Lift@10 |
|---|---:|
| 1 | 0.784x |
| 2 | 1.443x |
| 3 | 1.753x |
| 4 | 0.875x |

Resumen:

- media: **1.214x**;
- mediana: **1.159x**;
- folds > 1: **2/4**.

La lectura correcta no es “el modelo es estable en todos los meses”. La lectura correcta es:

> existe señal suficiente para superar el gate predefinido agregado, pero la heterogeneidad temporal sigue siendo un riesgo material.

## 8.3 Gate de promoción

El `stable_segment_logistic` se promueve si:

- mean Lift@10 > 1;
- median Lift@10 > 1;
- al menos 2/4 folds > 1;
- validation Lift@10 > 1;
- validation Brier no empeora materialmente frente al baseline constante.

En validation:

- Lift@10 = **1.442x**;
- Brier = **0.15611**;
- Brier baseline constante = **0.15691**.

Pasa el gate.

## 8.4 Holdout procedimental, no pristine

El holdout no se utilizó en el gate de promoción de esta ejecución, pero había sido inspeccionado en investigación previa.

Por tanto:

- sirve para evidencia retrospectiva;
- no debe describirse como completamente unseen;
- la confirmación real requiere nueva cohorte forward.

Fuentes:
- **Codexway base config**
- **Rolling model comparison**
- **Decisions**

---

# 9. Modelos evaluados dentro de Codexway

El benchmark canónico de Codexway es pequeño por diseño.

| Modelo | ROC-AUC holdout | PR-AUC | Brier | Lift@10 |
|---|---:|---:|---:|---:|
| Positive rate | 0.5000 | 0.2122 | 0.1672 | 1.000x |
| Business rule | 0.5157 | 0.2165 | 0.2501 | 0.986x |
| Logistic lead-only | 0.4823 | 0.2098 | 0.1733 | 0.932x |
| Logistic clean amplio | 0.4881 | 0.2156 | 0.1744 | 0.850x |
| Logistic sin asked_visit | 0.4852 | 0.2152 | 0.1743 | 0.987x |
| CatBoost | 0.4922 | 0.2086 | 0.2423 | 0.826x |
| **Stable segment logistic** | **0.5478** | **0.2391** | **0.1655 raw** | **1.689x** |
| **Selected calibrated** | **0.5478** | **0.2391** | **0.1658** | **1.689x** |

Conclusión:

- CatBoost no supera a la solución simple;
- más variables no garantizan mejor ranking;
- la señal que sí sobrevive al gate es de baja cardinalidad y concentrada.

Esto evita premiar complejidad por sí misma.

---

# 10. Modelo final

## 10.1 Arquitectura

Modelo:

**Regresión Logística regularizada**

Feature final:

`industrial_small_or_paid_interaction`

Definición:

`search_sector == "Industrial" AND (company_size == "small" OR source == "paid")`

Coeficiente estandarizado:

**+0.1204**

El efecto es positivo en el score, pero no se interpreta causalmente.

## 10.2 Por qué esta feature

La hipótesis fue elegida por:

- baja cardinalidad;
- disponibilidad ya desde T0;
- ausencia de mutable history;
- ausencia de geografía de alta cardinalidad;
- mejor concentración bajo capacidad;
- menor superficie de leakage;
- facilidad de explicación y monitoreo.

## 10.3 Granularidad del score

Después de Platt, el modelo produce esencialmente dos niveles observados en el holdout:

- **0.187899**
- **0.253098**

Esto es una fortaleza de gobernanza y una limitación de resolución.

No debe fingirse una granularidad que el modelo no posee.

---

# 11. Calibración

Codexway evalúa Platt scaling sobre validation.

Antes:

- Brier = 0.1561106;
- Log Loss = 0.4909444.

Después:

- Brier = **0.1560762**;
- Log Loss = **0.4908026**.

La mejora es pequeña, pero cumple la regla de retención: mejorar Brier o Log Loss.

En holdout:

- Brier seleccionado = 0.16577;
- Brier baseline de prevalencia = 0.16725;
- Brier skill score ≈ **0.0088**.

Tabla de calibración holdout:

| Predicción media | Tasa observada |
|---:|---:|
| 0.1879 | 0.1942 |
| 0.2531 | 0.3583 |

La segunda banda queda subcalibrada en el holdout: la tasa observada es mayor que la probabilidad predicha.

Eso refuerza que la calibración actual es útil pero no definitiva y debe revisarse con nueva evidencia forward.

Fuentes:
- **T1 model metrics**
- **Calibration table**

---

# 12. Evaluación adecuada para un problema de ranking desbalanceado

ROC-AUC se reporta, pero no es la métrica operativa principal.

La pregunta real es:

> si Growth sólo puede trabajar el top X% de leads, ¿cuántos positivos concentra?

Por eso se priorizan:

- PR-AUC;
- Precision@K;
- Recall@K;
- Lift@K;
- cumulative gains;
- Brier / Log Loss para probabilidad;
- estabilidad temporal;
- intervalos bootstrap.

## 12.1 Holdout

| Capacidad | Precision | Recall | Lift |
|---:|---:|---:|---:|
| 5% | 35.83% | 8.49% | **1.689x** |
| 10% | 35.83% | **16.98%** | **1.689x** |
| 20% | 28.37% | 26.80% | **1.337x** |

## 12.2 Gains

Al trabajar:

- 10% de la población, se captura 16.98% de positivos;
- 20%, se captura 26.80%;
- 30%, se captura 35.95%;
- 50%, se captura 54.25%.

La ganancia marginal cae conforme se amplía capacidad, como debe esperarse.

## 12.3 Tie-aware ranking

Debido a que existen muchos empates, Codexway **no usa row order como desempate**.

Si el límite de capacidad corta un bloque de scores idénticos, calcula expected capture fraccional uniforme.

Esto hace Lift@K:

- reproducible;
- invariante al orden físico de filas;
- coherente con una política operativa justa de tie-breaking.

Fuente:
- **evaluation.py**
- **Gains**

---

# 13. Incertidumbre

Bootstrap de 1,000 iteraciones sobre el holdout:

| Métrica | Estimación | IC95% |
|---|---:|---:|
| ROC-AUC | 0.5478 | [0.5273, 0.5684] |
| PR-AUC | 0.2391 | [0.2145, 0.2655] |
| Brier | 0.1658 | [0.1545, 0.1772] |
| Log Loss | 0.5129 | [0.4869, 0.5394] |
| Lift@5 | 1.689x | [1.381x, 1.983x] |
| Lift@10 | 1.689x | [1.381x, 1.982x] |
| Recall@10 | 16.98% | [13.88%, 19.92%] |
| Recall@20 | 26.80% | [23.91%, 29.76%] |

El intervalo de Lift@10 queda por encima de 1 en esta evidencia procedimental.

Sin embargo, la incertidumbre real no es sólo sampling uncertainty:

- el holdout histórico no es pristine;
- la feature estable fue formulada después de consumo global de evidencia;
- existe drift temporal fold-to-fold;
- el target es proxy;
- el score tiene baja resolución.

Por eso la recomendación final sigue siendo forward shadow.

---

# 14. Error analysis

El cutoff operacional derivado de validation es:

**0.2530980692**

Ese valor coincide con la banda alta del modelo.

En el archivo de error analysis del holdout:

- 120 false positives de prioridad;
- 296 false negatives;
- todos los false positives están en la banda 0.253098;
- todos los false negatives están en la banda 0.187899.

La lectura es directa:

1. el modelo no falla por pequeñas diferencias continuas de probabilidad;
2. falla porque su hipótesis de segmentación es demasiado gruesa;
3. dentro del segmento priorizado existe una fracción importante que no avanza;
4. fuera del segmento quedan muchos positivos no detectados.

Por tanto, la siguiente mejora real no consiste en afinar un threshold sobre los mismos dos scores. Requiere **nuevas señales PIT que separen mejor dentro y fuera del segmento**.

Fuente:
- **Error analysis**
- **Deployment readiness**

---

# 15. ¿Dónde funciona mejor y peor?

## 15.1 Sector

| Sector | N | AUC | AP | Lift@10 |
|---|---:|---:|---:|---:|
| Industrial | 434 | **0.616** | **0.318** | **1.401x** |
| Land | 281 | 0.500 | 0.192 | 1.000x |
| Office | 478 | 0.500 | 0.205 | 1.000x |
| Retail | 518 | 0.500 | 0.193 | 1.000x |

Esto es consistente con la arquitectura: la feature final sólo discrimina dentro del régimen Industrial.

Fuera de Industrial, el modelo es esencialmente un prior.

## 15.2 Modalidad

Lift@10:

- sale: **1.878x**;
- both: **1.715x**;
- rent: **1.461x**.

## 15.3 Source

Lift@10:

- organic: **1.852x**;
- referral: **1.492x**;
- paid: **1.438x**;
- email: **1.265x**;
- social: **1.206x**.

## 15.4 Channel

Lift@10:

- whatsapp: **2.131x**;
- app: **1.588x**;
- email: **1.439x**;
- web: **1.413x**.

Estas métricas son diagnósticas.

No significan que el modelo haya aprendido un efecto independiente de channel o modality: el predictor final sólo usa la interacción estable y los resultados segmentados reflejan cómo se distribuye esa banda de score dentro de cada subpoblación.

Fuente:
- **Segment metrics**

---

# 16. Estabilidad temporal

Lift@10 mensual en holdout:

| Mes 2026 | Lift@10 |
|---|---:|
| Enero | 1.207x |
| Febrero | 1.281x |
| Marzo | 2.554x |
| Abril | 1.432x |
| Mayo | 1.650x |
| Junio | 1.823x |

Todos los meses del holdout quedan por encima de 1, pero marzo es claramente atípico en magnitud.

La estabilidad temporal debe monitorearse con:

- prevalence;
- Lift@10;
- Recall@10/20;
- Brier;
- distribución del segmento Industrial-small/paid;
- PSI de la feature final;
- volumen y composición por source/sector.

Fuente:
- **Monthly stability**

---

# 17. Challengers: investigación por hipótesis

Esta sección demuestra amplitud de investigación sin convertir el assessment en un leaderboard incomparable.

## 17.1 Hipótesis: “un modelo no lineal generalista capturará mejor las interacciones”

**Experimento**

- CatBoost en Codexway;
- pooled CatBoost en experimentos históricos.

**Resultado**

En Codexway, CatBoost obtiene:

- PR-AUC 0.2086;
- Lift@10 0.826x;
- Brier 0.2423.

No supera al baseline ni al modelo estable.

En la línea histórica Modelo 3, pooled CatBoost fue competitivo y superó al multi-head bajo otro contrato experimental.

**Aprendizaje**

La familia CatBoost puede explotar señal en stacks más ricos, pero esa evidencia no autoriza reemplazar el modelo final bajo el contrato T1 de Codexway.

**Decisión**

No promover CatBoost en el entregable final.

---

## 17.2 Hipótesis: “modelos especialistas por etapa superarán una arquitectura compartida”

**Experimento**

EV-009 y EV-011 compararon:

- Multi-Head;
- specialist CatBoost;
- specialist Random Forest;
- pooled CatBoost + stage;
- híbridos seleccionados por validation.

**Resultado**

En rolling CV histórico, Specialist CatBoost y RF superaron al Multi-Head en macro AP, y T1 mostró señal favorable a especialistas tabulares.

Sin embargo:

- el stack usa otra población/snapshot architecture;
- la familia ganadora por etapa cambia fold a fold;
- el híbrido introduce selection risk;
- no constituye evidencia equivalente al T1 final de Codexway.

**Aprendizaje**

La hipótesis “más arquitectura = mejor” no se sostiene. Los tabulares simples suelen ser competitivos o superiores a multi-head.

**Decisión**

Mantener como evidencia de investigación; no sustituir el campeón Codexway.

Fuentes:
- **EV-009**
- **EV-011**

---

## 17.3 Hipótesis: “shared backbone + multi-head por etapa”

**Experimento**

EV-003.

**Resultado**

Multi-head mejoró al pooled neural inicial, pero después fue superado por familias tabulares en rolling temporal CV.

**Aprendizaje**

El resultado inicial fue útil como challenger arquitectónico, no como decisión final.

**Decisión**

Descartado como arquitectura canónica.

Fuente:
- **EV-003**

---

## 17.4 Hipótesis: “trajectory/progression agrega señal en T2”

**Experimento**

EV-012 y la réplica clean-room de AssessmentSol1.

**Resultado**

En la línea histórica:

- pooled CatBoost T2 ΔAP +0.0161, IC95% positivo;
- Multi-Head T2 ΔAP +0.0155, IC95% positivo.

En AssessmentSol1:

- T2 trajectory ΔAP ≈ +0.0032;
- sólo 2/4 folds mejoran;
- Brier y Log Loss empeoran ligeramente;
- no pasa su gate.

**Aprendizaje**

Trajectory puede ser útil en T2, pero es arquitectura- y contrato-dependiente.

**Decisión**

No contaminar T1 con features de historia futura. Mantener T2 como extensión.

Fuentes:
- **EV-012**
- **AssessmentSol1 T2 Decision**

---

## 17.5 Hipótesis: “Dynamic Need mejora el entendimiento del lead”

**Experimento**

EV-013.

**Resultado**

Dynamic Need K=5 produjo segmentación interpretable y una mejora puntual de Lift@10:

- 1.108x vs 1.001x en su baseline;
- ΔLift@10 +0.0993;
- IC95% cruza cero.

**Aprendizaje**

Dynamic Need es valioso para:

- segmentación;
- explicación;
- hipótesis de routing.

No demuestra mejora global robusta suficiente para formar parte del scorer final.

**Decisión**

Auxiliar/challenger, no feature canónica del Lead Quality final.

Fuente:
- **EV-013**

---

## 17.6 Hipótesis: “clusters y perfiles descubren pockets de conversión”

**Experimento**

EV-006, E007/E012/E015/E016.

**Resultado**

Se encontraron pockets locales, incluido:

`DN4 × LOC1 × BSV1`

con lift suavizado **1.510x** en su muestra.

Pero:

- hubo múltiples comparaciones;
- el mismo future test fue usado para discovery;
- no existe confirmación independiente;
- las mejoras globales entre challengers no se separan robustamente.

**Aprendizaje**

Los clusters son útiles para:

- interpretabilidad;
- generación de hipótesis;
- routing experimental;
- estratificación.

No deben convertirse en multiplicadores de score post-hoc.

**Decisión**

No forman parte del modelo final.

Fuentes:
- **EV-006**
- **Decision Segmentación**

---

## 17.7 Hipótesis: “semantic features derivadas con LLM aportan señal nueva”

**Experimento**

EV-017 con GPT-5 nano sobre 100 spots.

**Resultado**

En V2:

- costo ≈ USD 0.002579;
- new rule candidates: 0/100;
- residual actionable: 0/100.

La semántica reutilizable se expresó mejor como reglas determinísticas gratuitas.

**Aprendizaje**

El LLM aportó discovery metodológico, no una familia de features justificable para el ABT.

**Decisión**

No incluir `llm_*` en Lead Quality.

Fuente:
- **EV-017**

---

## 17.8 Hipótesis: “semantic rules gratuitas mejoran Lift@10”

**Experimento**

EV-018.

**Resultado**

Manteniendo target, folds, CatBoost e hiperparámetros:

- baseline Lift@10 macro: 1.267x;
- +Rules: 1.196x;
- ΔLift@10: **-0.0716x**;
- IC95% [-0.1438, +0.1251];
- P(Δ>0): 45%.

AP mejora sólo +0.0019 y AUC +0.0051.

**Aprendizaje**

Mover una métrica suave no basta si el objetivo operativo es concentración top-decile.

**Decisión**

Semantic Rules quedan para Inventory/Catalog QA, no scoring.

Fuente:
- **EV-018**

---

## 17.9 Hipótesis: “selected-Spot matching puede recuperar ranking”

**Experimento**

Recovery de AssessmentSol1.

**Resultado**

Su campeón `LQ_RECOVERY_R4_STATIC_MATCH_V1` utiliza:

- selected_spot_area_closeness;
- selected_spot_geographic_fit;
- selected_spot_attribute_completeness.

En DEVELOPMENT OOF de esa línea:

- Lift@10 1.075x;
- Lift@20 1.115x;
- 4/4 folds Lift@10 > 1;
- bootstrap ΔLift@10 amplio y cruzando cero.

**Aprendizaje**

Existe señal en selected-Spot context.

Pero AssessmentSol1 también reconoce que incorporar esta capa dentro de Lead Quality solapa la arquitectura con Inventory y obliga a revisar el score combinado.

**Decisión**

Se conserva como evidencia complementaria. Codexway mantiene Lead Quality separado de serviceability.

Fuente:
- **Recovery Decision**

---

## 17.10 Hipótesis: “response time explica mejor la calidad”

**Experimento**

EV-002.

**Resultado**

No aporta señal incremental robusta y, para la inquiry actual, ocurre después del scoring point.

**Aprendizaje**

Una variable puede parecer útil descriptivamente y ser inválida operacionalmente.

**Decisión**

`broker_response_hours` se excluye del scorer.

Fuente:
- **Assessment model component decisions**

---

# 18. Robustness checks

Se consideran robustez y sensibilidad en varios ejes.

## Temporal

- split cronológico;
- purges;
- rolling CV;
- estabilidad mensual.

## Target

- 7/14/30 días de maturity;
- accepted_or_scheduled;
- any scheduled inquiry 30d;
- T0/T2 como preguntas separadas.

## Features

- lead-only;
- lead + inquiry;
- sin asked_visit;
- interaction stable;
- CatBoost;
- clustering;
- semantic rules;
- selected-Spot challenger.

## Leakage

- feature allowlist;
- forbidden list;
- stress tests con internal score;
- future inquiry information;
- future/nearest availability;
- backward-as-of obligatorio.

## Calibration

- raw vs Platt;
- proper scoring rules;
- calibration table.

## Ranking

- tie-aware Lift;
- capacity 5/10/20%;
- bootstrap intervals.

---

# 19. Política operativa

## 19.1 Salida

`Lead Quality Score = 100 × calibrated_probability`

En el artefacto actual las bandas son aproximadamente:

- 18.79;
- 25.31.

## 19.2 Cutoff

El threshold de prioridad derivado del percentil 90 de validation es:

**p = 0.2530980692**

No debe interpretarse como cutoff universal de “buen lead”.

Es un punto de capacidad validado dentro de este dataset.

## 19.3 Capacidad

Codexway congela:

- default: top **10%**;
- escenarios: **5%, 10%, 20%**.

Si un empate cruza la frontera de capacidad:

- no usar row order;
- no usar un identificador arbitrario;
- usar desempate transparente/aleatorio o criterio operativo predefinido;
- mantener la medición tie-aware.

## 19.4 Activación

Estado:

**ELIGIBLE_AFTER_NEW_FORWARD_SHADOW_VALIDATION**

Secuencia recomendada:

1. shadow score sobre nueva cohorte;
2. esperar madurez del target;
3. recalcular Lift/Recall/calibración;
4. revisar drift;
5. si persiste la señal, A/B 50/50 sticky por `lead_id`;
6. análisis intention-to-treat.

Métrica primaria del piloto:

`scheduled_visit within 30 days`

Guardrails:

- time to first contact;
- contact attempts;
- broker workload;
- opt-out rate.

Fuente:
- **Deployment readiness**
- **Online A/B protocol**

---

# 20. Limitaciones

1. **Target proxy.** Scheduled visit no equivale a outcome comercial final.
2. **Holdout no pristine.** La evidencia final es retrospectiva.
3. **Baja resolución.** El score final tiene esencialmente dos bandas.
4. **Señal concentrada.** La discriminación está principalmente en Industrial.
5. **Weak rolling folds.** Dos de cuatro folds de promoción quedan bajo random.
6. **Synthetic/small dataset.**
7. **Feature hypothesis retrospectiva.**
8. **No causalidad.** Asociaciones predictivas no implican efecto causal.
9. **Inventory separado.** Lead Quality no dice si existe un Spot realmente atendible.
10. **No outcome de fallback.** No se puede calibrar Lead Quality contra éxito de recomendaciones alternativas.
11. **Unversioned listing state.** Parte de la información de Spots no tiene effective-time histórico.
12. **Nueva evidencia necesaria.** El paso siguiente correcto es validación forward, no más tuning sobre el mismo histórico.

---

# 21. Trazabilidad a evidencia

| Pregunta | Evidencia principal |
|---|---|
| Definición de Lead Quality | **Codexway README** |
| Scoring moment | **targets.py** |
| Maturity y splits | **base.yaml** |
| Feature allowlist | **feature_policy.yaml** |
| Leakage | **LEAKAGE_MATRIX.md** |
| Modelo final | **MODEL_CARD.md** |
| Métricas | **t1_model_metrics.json** |
| Incertidumbre | **t1_metric_intervals.csv** |
| Rolling CV | **rolling_model_comparison.csv** |
| Error analysis | **error_analysis.csv** |
| Estabilidad | **monthly_model_stability.csv** |
| Segmentos | **segment_metrics.csv** |
| Política operativa | **deployment_readiness.json** |
| Multi-head / especialistas | **EV-009**, **EV-011** |
| Trajectory | **EV-012** |
| Dynamic Need / clusters | **EV-013** |
| Semantic features | **EV-017**, **EV-018** |
| Auditoría temporal independiente | **AssessmentSol1 Temporal Semantics** |
| Recovery selected-Spot | **AssessmentSol1 Recovery** |

---

# 22. Tabla final de decisiones de modelado

| Decisión de modelado | Alternativas evaluadas | Evidencia | Razón de decisión |
|---|---|---|---|
| Scoring principal en T1 | T0, T1, T2 | Codexway + AssessmentSol1 | T1 equilibra señal contemporánea, cobertura y utilidad operativa sin condicionar a interacciones posteriores |
| Target = first inquiry scheduled_visit | accepted_or_scheduled, any scheduled 30d, targets T0/T2 | Codexway sensitivities + target audit | Proxy observable, simple y congelado antes de modelar |
| Maturity = 7d | 14d, 30d | Codexway target sensitivity | Contrato final de autoridad; sensibilidades no cambian el target post-hoc |
| ABT = una fila por lead en primera inquiry | snapshots multi-stage | targets.py + ABT | Grain operativo único, sin duplicar leads |
| Lead Quality separado de Inventory | selected-Spot matching, Availability dentro del scorer | Codexway architecture + AssessmentSol1 recovery | Evita doble conteo y conserva significado del componente |
| Feature policy explícita | ingestión automática de columnas | feature_policy + leakage matrix | Reduce leakage y hace auditable el information set |
| Modelo final = stable segment logistic | Business rule, broad logistic, CatBoost | rolling CV + validation + holdout procedimental | Única señal que supera el gate de concentración con complejidad mínima |
| No CatBoost final | CatBoost generalista / pooled / specialists | Codexway + EV-009/011 | No gana bajo contrato Codexway; resultados positivos históricos no son equivalentes |
| No multi-head | multi-head vs tabular | EV-003/009/011 | Tabulares superan al multi-head en CV histórico y el router por etapa es inestable |
| T2 trajectory no entra a T1 | 19/33 trajectory features | EV-012 + AssessmentSol1 T2 | Señal T2 dependiente de arquitectura y población; no corresponde al scoring T1 |
| Clusters auxiliares | Persona, Need, Dynamic Need, Physical, Location, Broker Service | EV-006/013 | Útiles para interpretación/routing hypothesis; sin lift global confirmado |
| No semantic rules en scorer | Rules-only, LLM-derived | EV-017/018 | No mejoran Lift@10; utilidad queda en QA de catálogo |
| No response time | Response-time RF | EV-002 | Post-treatment para inquiry actual y sin señal incremental robusta |
| Platt calibration | Raw | validation proper scoring | Mejora marginalmente Brier/Log Loss y se mantiene |
| Tie-aware capacity metrics | row-order top-k | E116/evaluation.py | Evita que empates hagan Lift dependiente del orden físico |
| Default capacity = 10% | 5%, 20% | config + gains | Punto operativo principal; escenarios adicionales quedan reportados |
| Threshold ≈ 0.2531 | 0.5, cutoff arbitrario | validation P90 | Derivado de capacidad/validation, no de convención de clasificación |
| Activación = forward shadow + A/B | automatización inmediata | deployment readiness | Holdout retrospectivo; hace falta confirmación independiente |

---

# 23. Riesgos metodológicos y mitigaciones

| Riesgo metodológico | Mitigación |
|---|---|
| Target leakage por broker response | Outcome excluido del feature set; sólo se usa para construir/evaluar target |
| Uso de información futura | Primera inquiry determinista; future inquiries prohibidas |
| Snapshot futuro de Availability | Backward as-of obligatorio; Availability fuera de Lead Quality |
| Mutable current-state fields | `days_on_market`, counters e `is_active` bloqueados |
| Internal score leakage | `lead_score_internal` sólo stress/benchmark, nunca clean model |
| Market Context sin publication time | EDA only |
| Texto/LLM sin version history | No entra al backtest de Lead Quality |
| Structural missingness | Tratamiento semántico en investigación; final model reduce exposición a este riesgo |
| Preprocessing leakage | Pipelines fit dentro de train/fold |
| Lead leakage entre folds | Splits temporales por entidad/lead |
| Ranking con scores empatados | Expected fractional capture / tie-aware metrics |
| Holdout históricamente consumido | Etiquetado como procedimental; nueva validación forward obligatoria |
| Multiple testing en clusters | Pockets tratados como hipótesis, no reglas |
| Selección post-hoc de semantic rules | E018 cierra la línea al fallar gate; no rescate sobre mismo OOF |
| Model-family shopping | Gate predefinido y benchmark pequeño en autoridad final |
| Calibration overfit | Calibración exclusivamente en validation |
| Threshold arbitrario | Percentil de validation y capacity-first policy |
| Drift temporal | Rolling CV + métricas mensuales + shadow monitoring |
| Causal overclaim | Todas las conclusiones se expresan como asociación predictiva |
| Doble conteo Lead Quality/Inventory | Arquitectura separada en Codexway |
| Exceso de confianza por una sola métrica | PR-AUC, Lift/Recall@K, Brier, temporal stability e intervalos bootstrap |

---

# 24. Respuestas directas a las 12 preguntas del evaluador

**1. ¿Qué significa Lead Quality?**  
Probabilidad de que la primera inquiry termine registrada como `scheduled_visit`; proxy de progreso temprano.

**2. ¿Cuándo se calcula?**  
En T1, inmediatamente después de persistir la primera inquiry y antes de la respuesta del broker.

**3. ¿Qué información puede conocerse válidamente?**  
Intake del lead, payload de la inquiry actual y transforms determinísticos disponibles a T1. No outcomes, futuro, current-state no versionado ni internal score.

**4. ¿Cómo se construye el target?**  
Primera inquiry determinista; positivo si su broker_response final es `scheduled_visit`; maturity de 7 días.

**5. ¿Cómo se evita leakage?**  
Allowlist, forbidden list, PIT ABT, splits temporales, fold-fit preprocessing, backward as-of y stress tests.

**6. ¿Por qué se eligió el modelo final?**  
Porque el `stable_segment_logistic` fue el único challenger canónico que superó el gate temporal de Lift@10 y proper scoring sin añadir complejidad innecesaria.

**7. ¿Qué alternativas se probaron?**  
Business rules, broad logistic, CatBoost, specialists, pooled models, multi-head, trajectory, Dynamic Need, clusters, selected-Spot matching, semantic rules y LLM features.

**8. ¿Por qué se descartaron?**  
Por falta de lift estable, no equivalencia contractual, riesgo temporal, complejidad sin evidencia incremental o solapamiento con Inventory.

**9. ¿Cómo se evalúa el ranking desbalanceado?**  
Con PR-AUC, Precision/Recall@5/10/20, Lift@5/10/20, cumulative gains, proper scoring y bootstrap.

**10. ¿Dónde funciona mejor y peor?**  
Mejor en Industrial y en subpoblaciones donde la banda alta se concentra; fuera de Industrial el modelo prácticamente no discrimina.

**11. ¿Qué incertidumbre tiene?**  
Lift@10 1.689x con IC95% [1.381, 1.982], pero con riesgo adicional por holdout retrospectivo, baja resolución y heterogeneidad temporal.

**12. ¿Cómo se usaría operativamente?**  
Como ranking de capacidad, inicialmente en shadow mode; default top 10%, cutoff validado ≈0.2531, desempate justo en ties y posterior A/B sticky por lead si la nueva cohorte confirma la señal.

---

## Conclusión

El valor de este Lead Quality Model no está en presentar un AUC espectacular.

Está en haber encontrado una señal de priorización **pequeña pero defendible**, después de descartar múltiples caminos más complejos, y en definir con precisión:

- qué se predice;
- cuándo;
- con qué información;
- qué no puede usarse;
- cómo se valida;
- cómo se mide incertidumbre;
- cuándo el modelo debe abstenerse de reclamar más de lo que demuestra.

La solución final de Codexway es, por tanto, una **capa de ranking conservadora, temporalmente explícita y preparada para confirmación forward**, no una promesa de automatización basada en un backtest retrospectivo.
