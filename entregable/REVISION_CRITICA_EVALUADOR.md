# Revisión crítica final — perspectiva del evaluador

## Dictamen ejecutivo

El paquete presenta una sola solución coherente con **Codexway como autoridad final**. La amplitud de `experimentos/**` aparece condensada como evidencia de decisiones y `AssessmentSol1/**` como auditoría metodológica; ninguno sustituye silenciosamente al champion.

La solución es defendible como assessment técnico y de producto. No es defendible todavía como un sistema listo para automatización plena, y el paquete lo reconoce explícitamente.

---

## Fortalezas

### 1. Contrato temporal claro

El scoring principal está congelado en **T1: primera inquiry, después de persistir el request y antes de broker response**.

El target final es:

**scheduled_visit en la primera inquiry, madurez 7 días.**

Esto evita que features posteriores al evento contaminen el modelo.

### 2. Leakage tratado como requisito de diseño

No se limita a “hacer split temporal”.

Se documentan y bloquean:

- broker response;
- future inquiries;
- current mutable listing state sin versionado;
- nearest/future Availability;
- market context sin publication time;
- internal score leakage.

Availability usa strict backward-as-of y reporta 0 future-snapshot violations.

### 3. Modelo final simple por una razón defendible

La baja complejidad del `stable_segment_logistic` puede parecer poco ambiciosa, pero el paquete demuestra que fue seleccionado frente a challengers por estabilidad temporal y concentración top-decile.

El resultado principal es útil para capacidad:

- Lead Quality Lift@10: **1.689x**;
- IC95%: **[1.381x, 1.982x]**.

### 4. Métricas alineadas al uso

No se vende AUC como única métrica.

Se usan:

- PR-AUC;
- Brier/Log Loss;
- Lift@K;
- Recall@K;
- calibration;
- temporal stability;
- tie-aware capacity metrics.

### 5. Inventory no se confunde con Lead Quality

El sistema conserva dos preguntas:

- ¿este lead tiene propensión a avanzar?
- ¿podemos atenderlo?

Eso permite reconocer que Opportunity puede mejorar “serviceability” sin necesariamente mejorar el target puro de conversión.

### 6. Fallback con abstención

La decisión **UNKNOWN ≠ UNAVAILABLE** y el uso de **NO_RESULT** son fortalezas de producto y governance.

Es preferible abstenerse que fabricar una recomendación.

### 7. Resultados negativos bien gobernados

El paquete no es una colección de winners.

Documenta decisiones negativas:

- CatBoost no promovido bajo el contrato final;
- semantic rules sin Lift incremental;
- LLM-derived features no promovidas;
- Inventory incremental gate NO-GO;
- pockets locales como hipótesis, no reglas.

Esto transmite seniority metodológico.

### 8. IA utilizada donde existe ventaja informacional

El LLM se probó con un caso real y costos reales.

La decisión de dejarlo fuera del predictor está respaldada por evidencia, no por omisión.

### 9. Producción y causalidad están separadas de claims offline

El siguiente paso es shadow + RCT, no “deploy porque Lift > 1”.

---

## Debilidades

### 1. Lead Quality tiene discriminación global modesta

ROC-AUC **0.5478** es bajo.

La defensa correcta no es ocultarlo, sino explicar que:

- la señal está concentrada;
- el uso es ranking bajo capacidad;
- Lift@10 es la métrica operacional principal;
- el modelo tiene baja resolución y no debe sobreinterpretarse.

### 2. El holdout no es completamente virgen

Codexway lo etiqueta como **procedural holdout** porque el histórico fue consumido globalmente durante la investigación.

Esto reduce fuerza confirmatoria.

La mitigación propuesta —forward shadow— es necesaria.

### 3. El target es un proxy temprano

`scheduled_visit` no es cierre ni valor comercial.

El sistema optimiza progreso comercial temprano, no revenue.

### 4. Inventory no demuestra valor incremental sobre el target T1

El Opportunity conservador:

- Lift@10 = **1.370x**;
- supera random;
- pero queda por debajo de Quality-only 1.689x.

El incremental Inventory gate es **NO-GO** para ese target.

La justificación del sistema combinado depende de un objetivo distinto: oportunidades que además sean servibles.

### 5. Matching histórico completo no es estrictamente PIT

Availability sí está defendida point-in-time.

Pero precio, área, geografía y otros atributos del listing no tienen un historial efectivo completo.

Por tanto el full matching histórico es condicional.

### 6. Fallback carece de gold label limpio

El Spot históricamente visitado no es un log de recomendaciones.

No puede interpretarse como ground truth de relevance.

### 7. Availability tiene coverage/freshness drift

Parte de la mejora aparente en períodos tardíos puede venir de mejor instrumentación del inventario, no de cambios reales del mercado.

### 8. LLM sin human gold completo

Se puede afirmar estabilidad técnica, costo y behavior sobre challenge.

No se puede afirmar precision/recall real sobre listings naturales.

---

## Preguntas difíciles que probablemente hará un evaluador

### “¿Por qué debería confiar en un modelo con AUC 0.55?”

Porque el caso de uso es ranking bajo capacidad, no clasificación perfecta. El evidence gate relevante muestra Lift@10 1.689x con intervalo bootstrap por encima de 1. Aun así, la baja resolución es una limitación y exige validación forward.

### “¿Por qué usar Opportunity si empeora Lead Quality?”

Porque son objetivos distintos. Si el objetivo es sólo scheduled_visit, se usa Quality-only. Si el objetivo es concentrar oportunidades que además puedan atenderse, Inventory entra como segundo eje. El paquete no afirma que Inventory ya mejore el target T1.

### “¿No estás double-counting Inventory?”

No en Codexway: el Lead Quality final no utiliza Availability ni selected-Spot serviceability. El Actionability Gate de AssessmentSol1 corresponde a otra arquitectura y aparece sólo como challenger.

### “¿Cuál es el K final: 3 o 5?”

**Top-3 interno** para agregar el componente de serviceability; **hasta 5 visibles** en fallback. K=3 visible fue un challenger histórico y no reemplaza la configuración final de Codexway.

### “¿La capacidad final es 10%, 15% o 20%?”

Codexway final: **top 10% default**, con escenarios 5/10/20%. P85/top15 y P80/top20 pertenecen a arquitecturas históricas de otras ramas y no son la política final.

### “¿El threshold 0.2531 es una frontera de negocio?”

No. Es el percentil de validation asociado a la capacidad final del dataset. La política es capacity-first; el cutoff no debe universalizarse.

### “¿Por qué usar un LLM si terminó fuera del modelo?”

Porque el requisito de IA se investigó en el dominio donde sí existe texto no estructurado. El LLM fue útil como semantic discovery; cuando no agregó información predictiva incremental, se evitó convertirlo en dependencia artificial.

### “¿Puedes afirmar que todo el matching es point-in-time?”

No. Se puede afirmar estrictamente para Availability. El matching completo queda condicionado por atributos del Spot sin versionado histórico.

### “¿Cuántos leads adicionales gana el sistema combinado?”

Codexway no tiene un gold causal/alineado para responder esa pregunta de forma limpia. Existe Lift absoluto del Opportunity Score, pero el valor incremental de Inventory queda no demostrado. La pregunta correcta debe resolverse online con exposure logs y RCT.

### “¿Por qué no usar el Spot que finalmente visitó el lead como gold?”

Porque no sabemos qué opciones fueron expuestas, recomendadas o disponibles bajo la misma política. Reproducir el Spot histórico podría aprender el proceso anterior, no relevance.

### “¿Por qué no desplegar ya?”

Por holdout retrospectivo, target proxy, listing state no versionado y ausencia de causalidad. El estado correcto es **eligible for forward validation**, no automatic deployment.

---

## Inconsistencias encontradas durante el cierre

| Inconsistencia/riesgo editorial | Resolución |
|---|---|
| Product Vision detallada excedía el máximo de 2 párrafos del assessment | Se creó [Product Vision ejecutiva](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md) como entry point oficial; el roadmap largo queda como anexo |
| No existía un One-Pager final dentro de `entregable/**` | Se creó [Entregable 2](02_one_pager/README.md) y su PDF de una página |
| `01_EDA.md` legado podía parecer la versión vigente | Se etiqueta como histórico y el índice maestro apunta exclusivamente a `01_eda/README.md` |
| P85/top15 y P80/top20 aparecen en evidencia histórica | Se mantienen sólo como challengers explícitos; la decisión final es top10 con escenarios 5/10/20 |
| K=3 vs K=5 | Reconciliado: top-3 interno de serviceability; máximo 5 recomendaciones visibles |
| Quality × Inventory vs Actionability Gate | Reconciliado: producto lower/upper es final Codexway; Gate es challenger de AssessmentSol1 bajo otro Lead Quality |
| Métricas E020 podían confundirse con performance final | Se mantienen etiquetadas como robustness check y no se mezclan con métricas Codexway |

---

## Blockers reales antes de entregar

### Blocker de paquete: deck ejecutivo

Existe `codexway/reports/slides.pdf`, pero este cierre no lo reconstruyó ni certificó editorialmente contra la narrativa final de `entregable/**`.

**Recomendación:** antes de enviar el assessment, revisar/actualizar el deck de 5–8 slides para que use exactamente:

- T1;
- maturity 7d;
- stable_segment_logistic;
- top10 default;
- top-3 interno / hasta 5 visibles;
- Opportunity lower de Codexway;
- Inventory incremental NO-GO;
- IA como Catalog QA discovery;
- forward shadow + RCT.

### No son blockers para enviar el assessment, pero sí para claims de producción

1. falta nueva validación forward independiente;
2. full historical listing state no está versionado;
3. fallback no tiene gold de exposure/acceptance;
4. no existe impacto causal online;
5. no existe human gold completo de Semantic QA.

---

## Conclusión del evaluador

**El paquete está técnicamente cerrado para evaluación, con una salvedad de presentación: revisar el deck PDF antes de usarlo.**

La mayor fortaleza no es una métrica aislada; es la disciplina con la que se separan:

- señal predictiva;
- observabilidad temporal;
- serviceability;
- incertidumbre;
- evidencia challenger;
- causalidad futura.

La solución no pretende ser más precisa de lo que la evidencia permite.
