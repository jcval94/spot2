# Descubrimientos acumulados — Spot2

Este documento consolida lo aprendido hasta ahora sin ocultar resultados negativos. Cada afirmación importante apunta a evidencia central y desde ahí a los artifacts originales.

## Resumen de estado

| ID | Estado | Descubrimiento | Evidencia |
|---|---|---|---|
| D001 | SUPPORTED | El re-scoring tras observar interacción contiene mucha más señal que el score frío T0 en el experimento inicial. | [EV-001](../Evidencias/EV-001_lead_attention.md) |
| D002 | NOT_SUPPORTED | El tiempo de respuesta del broker no aparece como driver predictivo robusto en estos datos sintéticos. | [EV-002](../Evidencias/EV-002_response_time_random_forest.md) |
| D003 | SUPPORTED | La arquitectura multi-head por etapa supera modestamente al modelo pooled en macro AP/AUC. | [EV-003](../Evidencias/EV-003_modelo_3_multihead.md) |
| D004 | SUPPORTED | En T2 la mayor dependencia predictiva viene del historial de interacción ya observable. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D005 | NOT_SUPPORTED | Los perfiles Lead × Spot × Broker iniciales no muestran sinergia robusta fuera de muestra. | [EV-005](../Evidencias/EV-005_entity_profile_match.md) |
| D006 | INCONCLUSIVE | Clustering balanceado produce perfiles mucho más interpretables, pero su lift predictivo sigue siendo pequeño e incierto. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D007 | PROPOSAL | Enriquecimiento geográfico externo tiene rutas plausibles, pero requiere joins point-in-time y validación incremental. | [EV-007](../Evidencias/EV-007_geographic_enrichment.md) |
| D008 | PROPOSAL | El LLM es defendible como capa de triage/extracción operativa; no existe evidencia en estos datos de lift causal del LLM. | [EV-008](../Evidencias/EV-008_llm_triage.md) |
| D009 | SUPPORTED | Separar Lead Persona de Search Need produce perfiles mucho más estables, balanceados y semánticamente claros, sin evidencia de lift incremental robusto. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D010 | NOT_SUPPORTED | Inquiry Intent v1 no debe usarse como capa predictiva: aprende principalmente día de la semana y empeora AP/AUC/lift fuera de muestra. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D011 | SUPPORTED | El perfil de Spot actual mezcla arquetipo físico con geografía; varios clusters son esencialmente regiones/estados. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D012 | INCONCLUSIVE | Existen bolsillos locales de compatibilidad Lead/Need × Spot × Broker con lift descriptivo, pero no hay evidencia suficiente de una sinergia global generalizable. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D013 | SUPPORTED | El drift temporal contiene una compresión sistemática de las interacciones hacia el alta del lead; timing requiere validación por cohortes. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |
| D014 | SUPPORTED | El dataset contiene clipping y redundancias sintéticas fuertes en área, presupuesto y precios de Spot. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |
| D015 | SUPPORTED | Los outliers son mayormente colas/regímenes de escala; no existe evidencia para borrarlos automáticamente y Isolation Forest debe ser diagnóstico. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |
| D016 | SUPPORTED | Market Context es un panel rotatorio e incompleto; el bajo coverage exacto es estructural y requiere semántica as-of. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |
| D017 | SUPPORTED | Availability es un estado dinámico del Spot, no un atributo estático. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |
| D018 | INCONCLUSIVE | El proxy scheduled_visit premia débilmente la compatibilidad económica/geográfica intuitiva; esto limita lo que el dataset puede demostrar sobre matching real. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |
| D019 | SUPPORTED | `days_on_market` y otros agregados actuales de Spot no forman una historia temporal coherente y deben bloquearse en scoring histórico. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |
| D020 | SUPPORTED | `prior_searches` y `prior_inquiries` son empíricamente casi independientes; no deben colapsarse mecánicamente en una sola noción de historial. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |
| D021 | INCONCLUSIVE | Existen diferencias descriptivas grandes entre brokers con soporte, pero todavía no separan efecto broker de composición de cartera/tiempo. | [EV-009](../Evidencias/EV-009_eda_profundo.md) |

## D001 — El modelo debe ser dinámico

**Estado:** SUPPORTED.

El experimento inicial de atención encontró:

- T0: ROC AUC 0.492, AP 0.527, Lift@10% 0.87x.
- T1 tras la primera inquiry: ROC AUC 0.632, AP 0.621, Lift@10% 1.22x.

La mejora no puede atribuirse únicamente a `urgency` o `asked_visit`: una ablación de esas señales no redujo el desempeño.

**Interpretación:** observar comportamiento/interacción cambia materialmente el information set y justifica re-scoring.

**No demuestra:** que cualquier feature de T1 sea causal ni que un LLM sea el responsable de la mejora.

Evidencia: [EV-001](../Evidencias/EV-001_lead_attention.md).

## D002 — Response time: señal operacional, no driver robusto

**Estado:** NOT_SUPPORTED.

En el análisis descriptivo, respuesta <=6h tuvo 19.64% de scheduled_visit frente a 21.21% con >24h.

El diagnóstico multivariable inicial apenas cambió AUC al añadir response time. El Random Forest posterior mostró que la variable puede aparecer en splits/MDI, pero la permutation importance es aproximadamente cero o negativa y el cambio contrafactual 2h→36h es pequeño.

**Interpretación:** no usar `broker_response_hours` como argumento central de poder predictivo en este dataset.

**Siguiente implicación:** si Spot2 considera el SLA una palanca de producto, probarlo causalmente mediante routing/SLA experimental.

Evidencia: [EV-002](../Evidencias/EV-002_response_time_random_forest.md).

## D003 — Shared backbone + heads por etapa sí aporta

**Estado:** SUPPORTED.

Modelo 3:

- multi-head macro AP: 0.5083;
- pooled macro AP: 0.4968;
- delta AP: +0.0115;
- multi-head macro AUC: 0.5330;
- pooled macro AUC: 0.5266;
- delta AUC: +0.0064.

T2 es la etapa con mayor señal del multi-head: AUC 0.595, AP 0.515, Lift@10% 1.39x.

**Interpretación:** compartir representación estadística, pero permitir comportamiento/calibración por etapa, es mejor que representar la etapa sólo como una feature pooled para este experimento.

**No demuestra:** superioridad universal de redes multi-head ni causalidad.

Evidencia: [EV-003](../Evidencias/EV-003_modelo_3_multihead.md).

## D004 — T2 obtiene su señal principalmente de historia observable

**Estado:** SUPPORTED.

Permutation importance por familias del head T2:

- `interaction_history`: ΔAP +0.0638, ΔAUC +0.0720;
- `spot_static`: ΔAP +0.0098;
- `availability_asof`: ΔAP +0.0074;
- `lead_intake`: ΔAP +0.0064.

La familia dominante se mantiene al usar únicamente el primer o último T2 por lead.

La variable individual más influyente del head fue la mediana histórica de horas de respuesta (ΔAP +0.0097), pero su dirección descriptiva no implica que responder más rápido cause mayor conversión.

**Interpretación:** el feature engineering futuro debe priorizar historia dinámica point-in-time, no acumular indiscriminadamente features estáticas.

Evidencia: [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md).

## D005 — La “química” Lead × Spot × Broker no está demostrada

**Estado:** NOT_SUPPORTED, con evidencia legacy superseded metodológicamente por D006.

La primera versión fue útil como exploración, pero la iteración posterior detectó look-ahead en la construcción histórica del perfil del broker. Sus resultados deben leerse como antecedente y no como prueba gobernada final.

En test futuro:

- perfiles marginales: AUC 0.503, AP 0.208;
- perfiles + interacciones: AUC 0.496, AP 0.206;
- delta AUC -0.006 con bootstrap 95% CI [-0.040, +0.023];
- delta AP -0.002 con bootstrap 95% CI [-0.013, +0.009].

Además, el clustering inicial produjo perfiles muy dominantes para Lead y Spot.

**Interpretación:** algunas combinaciones tienen tasas llamativas, pero no existe evidencia robusta de sinergia generalizable.

Evidencia: [EV-005](../Evidencias/EV-005_entity_profile_match.md).

## D006 — Clustering balanceado mejora perfiles, no prueba lift material

**Estado:** INCONCLUSIVE.

La segunda iteración corrigió el problema de clusters ~90% usando K-Means, Bisecting K-Means, BIRCH y GMM con selección por separación, balance y estabilidad.

Todos los perfiles seleccionados cumplen mínimo >=5% y máximo <=70%.

Predictivamente:

- global baseline AP 0.208;
- E001 balanced profiles AP 0.212;
- E002 lead facets AP 0.215;
- E003 inquiry intent AP 0.203.

E002 es el mejor por AP, pero los intervalos bootstrap de las mejoras incluyen cero. Añadir Inquiry Intent no mejoró el resultado.

**Interpretación:** Lead Persona, Search Need, Spot y Broker son representaciones interpretables útiles para análisis/matching, pero todavía no justifican afirmar mejora predictiva material.

**Hallazgo de diseño:** Availability Snapshot es mejor como estado temporal directo; Spot Attributes pertenece a Spot; Market Context requiere semántica de publicación antes de usarse como régimen.

Evidencia: [EV-006](../Evidencias/EV-006_profile_clustering_v2.md).

## D007 — Geografía externa: prometedora, todavía propuesta

**Estado:** PROPOSAL.

El market context existente mejoró sólo ligeramente T0 (aprox. +0.005 ROC AUC) y su cobertura exacta fue ~23%.

Las rutas más plausibles son INEGI municipal, DENUE, coordenadas/accesibilidad, CONAPO, Banxico y, para spots cuando sea posible, SEPOMEX.

**Restricción:** cualquier enriquecimiento histórico debe ser reproducible as-of scoring time.

Evidencia: [EV-007](../Evidencias/EV-007_geographic_enrichment.md).

## D008 — LLM: utilidad operacional todavía no lift demostrado

**Estado:** PROPOSAL.

Los datos no contienen el texto crudo de la inquiry, así que no puede medirse honestamente un LLM-vs-no-LLM.

El uso defendible es:

- extracción de intención y restricciones;
- resumen para broker;
- detección de información faltante;
- SLA recomendado;
- razón transparente de prioridad.

**No afirmar:** que el LLM incrementa conversión con la evidencia actual.

Evidencia: [EV-008](../Evidencias/EV-008_llm_triage.md).


## D009 — Persona y necesidad deben tratarse como facetas distintas

**Estado:** SUPPORTED para calidad de representación; **no** para lift incremental.

La descomposición de Lead en dos facetas produjo perfiles equilibrados y extremadamente estables:

- Lead Persona: K-Means, K=3, cluster mínimo 11.2%, máximo 51.4%, ARI 0.999.
- Search Need: K-Means, K=3, cluster mínimo 23.7%, máximo 46.3%, ARI 1.000.
- Persona separa principalmente quién es el actor (tenant_direct, broker, mayor historial de búsquedas).
- Search Need separa qué requiere (rent, sale, both, área/presupuesto).

Predictivamente E002 obtuvo AP 0.215 frente a 0.212 de E001, pero el delta bootstrap de AP fue +0.0028 con IC95% [-0.0134, +0.0185]; el delta de AUC también cruza cero.

**Interpretación:** para producto y feature engineering es más limpio representar **quién es el lead** y **qué necesita** por separado. Es una mejora semántica/estructural, no una mejora predictiva demostrada.

**No demuestra:** que Persona + Need aumenten conversión, ni que sean entidades físicas nuevas; son dos facetas latentes de la misma fila de Lead.

**Siguiente implicación:** conservar Persona y Search Need como features interpretables y evaluar sus interacciones con Spot/Broker sin convertirlas todavía en multiplicadores obligatorios del Opportunity Score.

Evidencia: [EV-006](../Evidencias/EV-006_profile_clustering_v2.md).

## D010 — Inquiry Intent v1 aprende calendario, no intención útil

**Estado:** NOT_SUPPORTED.

El clustering de Inquiry Intent quedó técnicamente balanceado (GMM, K=7, mínimo 6.5%, máximo 26.0%, ARI 0.737), pero seis de siete perfiles están dominados por el día de la semana. Sólo un perfil destaca de forma clara por área/presupuesto solicitados muy altos.

Al añadir Inquiry Intent a E002:

- AUC: 0.513 → 0.491.
- AP: 0.215 → 0.203.
- Lift@10%: 1.023x → 0.905x.
- Delta AUC bootstrap: -0.020, IC95% [-0.044, +0.002].
- Delta AP bootstrap: -0.0106, IC95% [-0.0261, +0.0036].
- Delta Lift@10%: -0.142, IC95% [-0.361, +0.080].

**Interpretación:** clusters diferenciados no son suficientes; pueden capturar una partición estadística estable pero irrelevante para negocio.

**No demuestra:** que la información T1 de la inquiry sea inútil. Demuestra que **esta definición v1 del perfil** no aporta.

**Siguiente implicación:** si se retesta Inquiry Intent, excluir weekday y centrar el espacio de clustering en asked_visit, urgency_days, canal, área/presupuesto solicitado, desviación contra Search Need y longitud del mensaje.

Evidencia: [EV-006](../Evidencias/EV-006_profile_clustering_v2.md).

## D011 — Spot mezcla “qué es” con “dónde está”

**Estado:** SUPPORTED.

El Spot balanceado usa Bisecting K-Means con K=7 (mínimo 9.5%, máximo 27.3%), pero la interpretabilidad muestra que varios perfiles están dominados por ubicación:

- S2: CDMX / región centro.
- S3: Bajío / Querétaro.
- S5: Nuevo León / San Pedro Garza García.
- S6: Estado de México / Naucalpan.
- S7: Jalisco / Zapopan.
- S4 es una excepción más física, distinguida por piso alto y mayor número de elevadores.

**Interpretación:** el cluster actual de Spot representa parcialmente mercado/localización, no sólo tipo físico de inmueble.

**No demuestra:** que geografía deba eliminarse. Geografía es claramente relevante para matching; el problema es confundirla con el arquetipo físico.

**Siguiente implicación:** probar por separado **Physical Space Archetype** y **Location / Market Regime**, manteniendo disponibilidad como estado temporal directo.

Evidencia: [EV-006](../Evidencias/EV-006_profile_clustering_v2.md).

## D012 — Hay compatibilidades locales, pero no una “química” global demostrada

**Estado:** INCONCLUSIVE.

En el future test aparecen celdas descriptivamente atractivas:

- L1 × S1 × B5: n=93, scheduled_visit 30.1%, tasa suavizada 27.3%, lift 1.31x.
- N2 × S3: n=197, scheduled_visit 25.4%, lift 1.18x.
- N1 × S5: n=157, scheduled_visit 24.8%, lift 1.16x.
- N1 × S6: n=172, scheduled_visit 24.4%, lift 1.14x.

Sin embargo, el modelo global de perfiles sólo alcanza lift@10% 1.033x (E001) y 1.023x (E002), y las mejoras entre representaciones no son robustas en bootstrap.

**Interpretación:** sí existen **bolsillos locales de matching** que merecen estudio, especialmente Search Need × Spot, pero todavía no justifican un Compatibility Score multiplicativo general.

**No demuestra:** causalidad, estabilidad futura de cada celda ni que el broker “cause” la diferencia observada.

**Siguiente implicación:** usar las matrices Need × Spot y Need × Broker como hipótesis de routing, exigir soporte mínimo/intervalos de confianza y validar después con diseño online o cuasi-experimental.

Evidencia: [EV-006](../Evidencias/EV-006_profile_clustering_v2.md).


## D013 — El drift temporal contiene compresión de interacción

**Estado:** SUPPORTED.

El total de inquiries por lead permanece relativamente estable (~4.2–4.8), pero las inquiries dentro de los primeros 30 días pasan de 1.37 por lead en 2025-01 a >4.1 en 2026-05/06. La mediana de tiempo a primera inquiry cae de 7.82 a ~2.31 días.

**Interpretación:** el aumento temporal del proxy no es sólo un cambio de prevalencia; existe un cambio en la mecánica temporal del proceso. Features como `days_from_lead_creation` pueden capturar cohort/generator drift.

**No demuestra:** causalidad ni que la velocidad de interacción deba manipularse operacionalmente.

**Siguiente implicación:** toda feature temporal debe evaluarse por cohortes y con validación estrictamente temporal.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).

## D014 — El dataset contiene clipping y redundancias sintéticas

**Estado:** SUPPORTED.

El EDA profundo encuentra:

- ~35.5% de `requested_area / spot_area` cerca de 0.30;
- ~21.4% cerca de 5.00;
- ~25.1% de requested rent exactamente en el max rent del lead;
- ~24.7% de requested sale exactamente en el max sale;
- `spot price_total ≈ area × price_sqm` con error relativo p99 casi cero.

**Interpretación:** varias columnas contienen reglas explícitas del generador y no representan grados de libertad independientes.

**No demuestra:** que deban eliminarse automáticamente. Sí obliga a evitar interpretaciones ingenuas y a probar redundancia/ablation en feature engineering.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).

## D015 — Los outliers son mayormente colas de régimen, no suciedad demostrada

**Estado:** SUPPORTED.

Áreas, precios totales, mantenimiento e historial previo presentan colas muy largas. Tukey marca frecuentemente 7–13% o más dentro de sector × modalidad.

Isolation Forest, usado con 3% de contamination sólo como diagnóstico, marca 155 leads, 94 spots y 685 inquiries. En la implementación reproducible, el 25.8% de leads, 46.8% de spots y 41.9% de inquiries marcadas tienen además algún extremo univariado dentro del mismo régimen, frente a 3.7%, 5.2% y 3.7% respectivamente entre no marcadas.

El anomaly score tampoco funciona como Opportunity Score: el top 1% más anómalo tiene 17.95% de scheduled_visit vs 19.94% en el resto; top 3% 19.12% vs 19.94%; top 5% 19.38% vs 19.94%.

**Interpretación:** el bosque identifica rareza multivariable real, pero no una población clara de errores ni de oportunidades.

**Siguiente implicación:** preferir log/robust representations y revisión de casos; no winsorizar o borrar automáticamente.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).

## D016 — Market Context es un panel incompleto

**Estado:** SUPPORTED.

Existen 72 claves geo-sector y 30 meses globales, pero cada clave aparece sólo 3–12 meses, mediana ~7, y ninguna cubre el periodo completo.

**Interpretación:** el ~23% de cobertura exacta observado en el EDA base es estructural. El panel no admite forward-fill ingenuo sin saber publicación y disponibilidad histórica.

**Siguiente implicación:** definir explícitamente el as-of del contexto o usar el último periodo cerrado/publicado conocido.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).

## D017 — Availability es un estado dinámico

**Estado:** SUPPORTED.

~90.3% de los spots cambia de disponibilidad al menos una vez; la mediana es ~4 transiciones con ~10 snapshots por spot. La separación entre snapshots tiene mediana de 21 días, p95 de 97, p99 de 155 y máximo de 319 días.

**Interpretación:** Availability debe conservarse como estado point-in-time, con una medida explícita de staleness/edad del snapshot, y no incorporarse como atributo permanente del arquetipo Spot.

**No demuestra:** que disponibilidad sea predictiva de Lead Quality; de hecho, el EDA base mostró una asociación casi plana con ese proxy.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).

## D018 — El proxy premia débilmente la compatibilidad intuitiva

**Estado:** INCONCLUSIVE respecto al matching real.

En scheduled_visit las coincidencias de estado/municipio/corredor sólo mueven aproximadamente 1 pp en crudo. Los buckets de área y presupuesto tampoco favorecen consistentemente el fit cercano a 1.

**Interpretación:** este target sintético está débilmente acoplado a una definición simple de compatibilidad económica/geográfica, lo que ayuda a explicar el bajo lift global de EV-005/EV-006.

**No demuestra:** que el matching sea irrelevante en producción. Puede ser una limitación del proxy/generador.

**Siguiente implicación:** evaluar ranking/matching con objetivos más cercanos a calidad de match o validación online, no concluir sólo desde scheduled_visit.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).


## D019 — Los agregados actuales de Spot no reconstruyen una historia temporal coherente

**Estado:** SUPPORTED.

El final observable del dataset es 2026-07-13. Si se interpreta literalmente `created_at + days_on_market`, 373 spots (12.43%) implican una fecha posterior al final observable; 17 quedan a más de un año en el futuro. El p99 del desfase es +308 días y el máximo +694 días.

Además, `spots.total_inquiries` coincide exactamente con el conteo observable de `inquiries` en sólo 7.07% de los spots.

**Interpretación:** `days_on_market`, `total_inquiries`, `total_views` e `is_active` deben tratarse como current-state/synthetic aggregates, no como snapshots históricos reconstruibles.

**Siguiente implicación:** mantenerlos bloqueados en T0/T1/T2 salvo que exista una reconstrucción point-in-time demostrable.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).

## D020 — prior_searches y prior_inquiries no son dos versiones de la misma historia

**Estado:** SUPPORTED descriptivamente.

`prior_searches` tiene 34.5% de ceros y `prior_inquiries` 44.4%. Su correlación Pearson es **-0.00495**, prácticamente cero, pese a que los nombres sugieren actividad relacionada.

**Interpretación:** en este dataset representan procesos distintos o fueron generadas casi independientemente.

**Siguiente implicación:** no sumarlas, promediarlas ni convertirlas en un único “engagement histórico” sin validar primero su semántica y su aporte incremental.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).

## D021 — Broker muestra heterogeneidad descriptiva, todavía no efecto broker

**Estado:** INCONCLUSIVE respecto a causalidad o feature value.

Entre brokers con al menos 50 inquiries, la tasa observada de scheduled_visit varía aproximadamente de **9.86% a 32.79%**.

**Interpretación:** existe suficiente dispersión para justificar un experimento posterior de perfil histórico de broker, pero una tasa full-dataset mezcla geografía, tipo de spot, cartera, lead mix y tiempo.

**Siguiente implicación:** si se construye un broker prior, hacerlo point-in-time, con shrinkage/regularización y validación temporal; comparar contra una baseline sin identidad de broker.

Evidencia: [EV-009](../Evidencias/EV-009_eda_profundo.md).
