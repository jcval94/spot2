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
| D009 | INCONCLUSIVE | Search Need sí queda semánticamente limpio; Lead Persona actual está dominado por canal de adquisición/historial, por lo que la separación de facetas es correcta pero Persona necesita rediseño. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D010 | NOT_SUPPORTED | Inquiry Intent v1 no debe usarse como capa predictiva: aprende principalmente día de la semana y empeora AP/AUC/lift fuera de muestra. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D011 | SUPPORTED | El perfil de Spot actual mezcla arquetipo físico con geografía; varios clusters son esencialmente regiones/estados. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D012 | INCONCLUSIVE | Existen bolsillos locales de compatibilidad Lead/Need × Spot × Broker con lift descriptivo, pero no hay evidencia suficiente de una sinergia global generalizable. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md) |
| D013 | SUPPORTED | La ventaja puntual inicial de RF sobre el head T2 fue confirmada posteriormente con rolling temporal CV; ver D021/D034. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md), [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md) |
| D014 | SUPPORTED | La señal T2 se interpreta mejor como trayectoria/progreso vs estancamiento que como efecto de la inquiry actual aislada. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D015 | SUPPORTED | Condicionada al historial observable, la inquiry actual y el match Lead↔Spot aportan poca señal incremental promedio en T2, aunque recuperan valor en el último T2. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D016 | INCONCLUSIVE | `availability_snapshot_age_days` aparece predictiva, pero su dirección es sospechosa y puede estar capturando estructura temporal/cobertura en lugar de disponibilidad accionable. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D017 | SUPPORTED | La baja concordancia entre rankings del multi-head y RF indica que las conclusiones más robustas son por familias, no por ranking exacto de variables individuales. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D018 | INCONCLUSIVE | E005 con un único holdout no separó robustamente Multi-Head de challengers fuertes; esta incertidumbre queda resuelta por rolling CV en D034. | [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md) |
| D019 | SUPPORTED | T1 favorece especialistas tabulares no lineales sobre el head T1; el hallazgo de RF se replica con rolling CV y CatBoost también supera robustamente al Multi-Head. | [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md), [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md) |
| D020 | SUPPORTED | Rolling CV confirma que un CatBoost pooled con stage supera al Multi-Head tanto en AUC macro como en AP macro. | [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md), [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md) |
| D021 | SUPPORTED | Rolling CV confirma que T2 contiene señal explotable por especialistas tabulares: CatBoost y RF superan robustamente al Multi-Head en AP y AUC. | [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md) |
| D022 | INCONCLUSIVE | El híbrido seleccionado por validation supera robustamente al Multi-Head en OOF, pero la familia elegida por etapa cambia entre folds; no es una arquitectura estable para producción. | [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md) |
| D023 | INCONCLUSIVE | Separar Spot en Physical Space + Location mejora fuertemente la interpretabilidad, pero no demuestra lift predictivo frente al Spot unificado. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D024 | INCONCLUSIVE | Compatibility Routing mejora puntos lead-level y revela celdas atractivas, pero el delta AP pre-registrado sigue cruzando cero. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D025 | SUPPORTED | La integridad relacional es limpia, pero Availability exige backward as-of: un join directo por spot_id expande las inquiries ~10.02x. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D026 | SUPPORTED | Modalidad funciona como restricción dura; sector, municipio y corredor se comportan como preferencias blandas en el matching observado. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D027 | SUPPORTED | El Need evoluciona entre Lead e Inquiry: presupuesto y área se refinan materialmente en T1. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D028 | SUPPORTED | El missingness de presupuesto/precio es mayormente estructural por modalidad y la aritmética de precios del Spot es internamente consistente. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D029 | NOT_SUPPORTED | broker_response_hours no puede tratarse como un SLA limpio: su presencia no concuerda semánticamente con broker_response. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D030 | SUPPORTED | Availability es consistente pero su cobertura cambia drásticamente en el tiempo; debe tratarse como riesgo de coverage drift/censoring. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D031 | NOT_SUPPORTED | Market Context no está listo para uso histórico point-in-time: la cobertura exacta es ~23.8% y no existe semántica de publicación/effective time. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D032 | INCONCLUSIVE | Existen bolsillos locales de compatibilidad de hasta ~1.37x lift suavizado, pero no hay evidencia suficiente para un Compatibility Score global. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D033 | NOT_SUPPORTED | spots.total_inquiries no equivale al conteo de la tabla inquiries y no debe usarse como historial de eventos sin redefinir su semántica. | [EV-010](../Evidencias/EV-010_matching_ab_v3.md) |
| D034 | SUPPORTED | Rolling temporal CV resuelve la incertidumbre de E005: modelos tabulares no lineales superan robustamente al Multi-Head; specialist CatBoost obtiene el mejor macro AP OOF puntual. | [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md) |
| D035 | SUPPORTED | Features explícitas de trayectoria mejoran T2 de forma robusta en pooled CatBoost y Multi-Head bajo los mismos folds temporales. | [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md) |
| D036 | NOT_SUPPORTED | Las trajectory features no son universalmente beneficiosas: empeoran significativamente el AP T2 del Random Forest y no mejoran de forma robusta al CatBoost especialista. | [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md) |
| D037 | INCONCLUSIVE | La selección de una familia distinta por etapa es inestable entre folds; la complejidad del híbrido no queda justificada frente a una base CatBoost más simple. | [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md), [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md) |
| D038 | PROPOSAL | Separar Acquisition Channel de Behavioral Maturity puede producir una Persona más interpretable y menos dominada por source. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D039 | PROPOSAL | Un Dynamic Need T1 sin weekday puede capturar refinamiento de área/presupuesto y mejorar lift frente al Need T0 estático. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D040 | PROPOSAL | Broker Supply + Broker Service sin response_hours puede mejorar interpretabilidad y compatibilidad frente al Broker legacy. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D041 | PROPOSAL | Matching jerárquico sobre perfiles rediseñados puede superar el E007 flat compatibility y revelar pockets de lift más altos. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D042 | PROPOSAL | Dynamic Need debe probarse directamente sobre E006 para aislar su efecto del deterioro introducido por E008 Persona. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D043 | PROPOSAL | Broker Supply/Service necesita una versión compacta, winsorizada y con gate duro de balance antes de considerarse una segmentación válida. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D044 | PROPOSAL | La jerarquía v2 sólo debe evaluarse sobre la rama fuerte E012→E013 y compararse contra E007 en el mismo future test. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |

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


## D009 — Persona y Search Need sí son facetas distintas, pero Persona aún no es una persona comercial limpia

**Estado:** INCONCLUSIVE.

El rerun autoritativo de profile_clustering_v2 confirma que separar “quién / madurez” de “qué necesita” es conceptualmente correcto, pero cambia la interpretación material de Persona.

**Search Need sí es limpio:**

- N1: renta (99% rent).
- N2: venta (100% sale).
- N3: modalidad both (83%) y mayor área objetivo.

**Lead Persona actual está dominado por canal/historial:**

- P1 organic.
- P2 paid.
- P3 referral.
- P4 prior_searches alta.
- P5 has_converted_before + prior_inquiries alta.
- P6 email.
- P7 social.

E002 tampoco mejora robustamente a E001 en la corrida actual: ΔAP -0.0068, IC95% [-0.0224, +0.0072].

**Interpretación:** Search Need puede mantenerse como estado de demanda. Persona debería rediseñarse como dos facetas explícitas —Acquisition Channel y Behavioral Maturity— antes de usar etiquetas de negocio más fuertes.

**Refina:** la versión previa de D009 que describía Persona como semánticamente limpia.

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


## D013 — El multi-head no gana T2 contra especialistas no lineales

**Estado:** SUPPORTED; observación inicial posteriormente confirmada por rolling CV.

En el mismo test temporal T2:

- Multi-head T2: ROC AUC 0.595, AP 0.515, Lift@10% 1.39x.
- Random Forest T2: ROC AUC 0.609, AP 0.524, Lift@10% 1.43x.

**Interpretación:** D003 sigue siendo válido frente al challenger pooled y las regresiones separadas, pero no debe generalizarse a “multi-head es la mejor familia”. Un especialista tabular no lineal ya produjo una mejora pequeña.

El diagnóstico inicial no era suficiente para declarar ganador. E006 posteriormente confirmó con rolling temporal CV que RF y CatBoost T2 superan al Multi-Head con intervalos completamente positivos; la conclusión gobernada final está en D021/D025.

Evidencia inicial: [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md). Confirmación: [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md).

## D014 — T2 captura trayectoria: progreso vs estancamiento

**Estado:** SUPPORTED como interpretación predictiva.

La familia `interaction_history` domina en todos los T2 (ΔAP +0.0638). La dominancia se conserva usando una sola observación por lead:

- primer T2 por lead: ΔAP +0.0471;
- último T2 por lead: ΔAP +0.0757.

Además, más respuestas ya observadas no equivalen a mejor resultado futuro: leads con <=1 respuesta histórica tuvieron 49.2% de visita futura frente a 36.2% con >=2; patrones similares aparecen para respuestas aceptadas sin visita posterior.

**Interpretación:** el modelo parece reconocer una trayectoria del funnel: la acumulación de interacciones sin visita puede ser señal de fricción o estancamiento, no sólo de intención.

**No demuestra:** que provocar más o menos interacciones cause conversión; el patrón está condicionado por la definición pre-visita de T2.

Evidencia: [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md).

## D015 — La última inquiry aporta menos que la trayectoria acumulada

**Estado:** SUPPORTED para este head y población T2.

Permutation importance por familias sobre todos los T2:

- `current_inquiry`: ΔAP -0.0024;
- `lead_spot_match`: ΔAP -0.0012;
- `interaction_history`: ΔAP +0.0638.

En el último T2 por lead, la inquiry actual y el match sí recuperan señal (aprox. +0.0077 y +0.0074 AP), pero siguen muy por debajo del historial (+0.0757).

**Interpretación:** una vez existe historia suficiente, el estado acumulado del proceso pesa más que una sola interacción.

**No demuestra:** que inquiry o matching sean inútiles en T0/T1, ni que deban eliminarse del producto.

Evidencia: [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md).

## D016 — La edad del snapshot de disponibilidad requiere auditoría

**Estado:** INCONCLUSIVE.

`availability_snapshot_age_days` fue la tercera variable individual del head T2 por permutation importance (ΔAP +0.0070), pero el perfil descriptivo fue contraintuitivo: snapshots más viejos presentaron mayor tasa de visita futura que snapshots recientes.

**Interpretación:** puede estar actuando como proxy de periodo, cobertura de inventario, corredor o mecanismo sintético de generación de datos, no como una palanca de disponibilidad.

**No demostrar / no hacer:** no interpretar “información más vieja es mejor” ni usar la variable como regla operativa hasta realizar una auditoría temporal específica.

Evidencia: [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md).

## D017 — Confiar en familias, no en el ranking exacto

**Estado:** SUPPORTED.

La concordancia de rankings fue modesta:

- Spearman multi-head vs RF permutation: 0.245;
- Spearman multi-head vs RF MDI: 0.259.

Sin embargo, ambos modelos señalan variables de tiempo/progreso/historial como relevantes y el análisis por familias del propio head es estable al cambiar la muestra T2 por lead.

**Interpretación:** las conclusiones de negocio deben apoyarse en bloques de información y ablations, no en afirmar que una variable individual es universalmente “la #1”.

Evidencia: [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md).

## D018 — No hay ganador global robusto por macro AP

**Estado:** INCONCLUSIVE.

E005 mantuvo target, población, features y split de E003 sin cambios (comparación `EQUIVALENT`).

Resultados macro AP:

- Multi-Head: 0.5083.
- mejor especialista fijo, Random Forest: 0.5175; delta +0.0092.
- pooled CatBoost + stage: 0.5242; delta +0.0159.
- híbrido elegido sólo con validation: 0.5295; delta +0.0212.

Sin embargo:

- RF vs Multi-Head: IC95% AP [-0.0173, +0.0394].
- pooled CatBoost vs Multi-Head: IC95% AP [-0.0080, +0.0438].
- híbrido vs Multi-Head: IC95% AP [-0.0059, +0.0520].

**Interpretación:** la ventaja puntual favorece modelos tabulares fuertes, pero la métrica primaria no permite declarar un ganador global con confianza.

**No demuestra:** que Multi-Head sea equivalente en producción ni que la arquitectura de heads sea innecesaria; sólo que el test actual no separa robustamente sus macro AP.

Evidencia: [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md).

## D019 — T1 favorece especialistas tabulares no lineales

**Estado:** SUPPORTED y replicado con rolling temporal CV.

E005 encontró ventaja de Random Forest sobre el head T1. E006 la replica en 7,980 predicciones OOF / 1,936 leads:

- RF vs Multi-Head: ΔAP +0.0337, IC95% [+0.0105, +0.0561].
- RF vs Multi-Head: ΔAUC +0.0427, IC95% [+0.0181, +0.0691].
- Specialist CatBoost vs Multi-Head: ΔAP +0.0404, IC95% [+0.0128, +0.0687].
- Specialist CatBoost vs Multi-Head: ΔAUC +0.0596, IC95% [+0.0342, +0.0858].

CatBoost tiene mejor punto OOF que RF en T1, pero la diferencia AP directa CatBoost−RF no queda demostrada con robustez.

**Interpretación:** T1 sí tiene señal; el problema era la representación/modelo del head, no la ausencia de información en la primera interacción.

Evidencia inicial: [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md). Confirmación CV: [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md).

## D020 — Un solo CatBoost fuerte con stage supera al Multi-Head

**Estado:** SUPPORTED en rolling temporal CV.

E005 ya sugería ventaja en AUC. E006 la confirma también para la métrica primaria:

- pooled CatBoost macro AP 0.4665 vs 0.4498 Multi-Head; ΔAP +0.0167, IC95% [+0.0016, +0.0315].
- pooled CatBoost macro AUC 0.5721 vs 0.5498; ΔAUC +0.0223, IC95% [+0.0077, +0.0371].

**Interpretación:** varios heads no son necesarios para representar la etapa. Un learner tabular fuerte puede aprender interacciones `stage × history × inquiry × spot` y superar al backbone multi-head actual.

**Implicación de ingeniería:** pooled CatBoost + stage es un baseline de producción más simple que tres heads, salvo que un especialista por etapa justifique su complejidad con evidencia adicional.

Evidencia: [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md), [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md).

## D021 — T2 favorece especialistas tabulares sobre el Multi-Head

**Estado:** SUPPORTED tras rolling temporal CV.

E006 resuelve la incertidumbre del single holdout:

- Specialist CatBoost vs Multi-Head T2: ΔAP +0.0332, IC95% [+0.0088, +0.0594]; ΔAUC +0.0418, IC95% [+0.0191, +0.0671].
- Specialist RF vs Multi-Head T2: ΔAP +0.0278, IC95% [+0.0059, +0.0505]; ΔAUC +0.0280, IC95% [+0.0073, +0.0491].
- pooled CatBoost T2 mejora AUC robustamente (+0.0381) pero su ΔAP +0.0229 todavía tiene IC95% [-0.0029, +0.0516].

CatBoost tiene el mejor punto OOF T2, pero CatBoost−RF en AP no es robusto; no hay evidencia para afirmar que uno de esos dos sea definitivamente superior por AP.

**Interpretación:** D004/D014 siguen explicando **qué** contiene señal (historia/trayectoria), mientras E006 muestra que árboles/boosting la explotan mejor que el head T2 actual.

Evidencia: [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md).

## D022 — El híbrido mejora, pero su composición no es estable

**Estado:** INCONCLUSIVE como arquitectura de producción.

En E006, el híbrido seleccionado dentro de cada fold supera al Multi-Head en OOF:

- Δ macro AP +0.0181, IC95% [+0.0019, +0.0339].
- Δ macro AUC +0.0236, IC95% [+0.0080, +0.0404].

Sin embargo, la familia seleccionada cambia entre folds. En E006 T1 alterna CatBoost/LightGBM y T2 alterna pooled CatBoost/specialist CatBoost; en E007 la selección vuelve a cambiar.

**Interpretación:** existe heterogeneidad por etapa, pero un meta-selector de familias añade complejidad y selection bias sin una composición suficientemente estable.

**Implicación:** preferir una base fija CatBoost fuerte y mantener especialistas como challengers/overrides sólo cuando la mejora sea consistente.

Evidencia: [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md), [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md).


## D023 — Separar Spot físico de localización mejora la semántica, no el lift demostrado

**Estado:** INCONCLUSIVE.

E006 comparó, sobre exactamente la misma población y split:

- **A / control:** Persona + Search Need + Broker + Unified Spot + Availability.
- **B / tratamiento:** Persona + Search Need + Broker + Physical Space + Location + Availability.

La descomposición produjo perfiles mucho más legibles:

- Physical: 4 clusters; PH2 es 100% Industrial, PH3 100% Land.
- Location: 7 clusters geográficos, ARI=1.000.

Pero el rendimiento no mejora de forma robusta:

- AP A 0.2100 vs B 0.2098.
- ΔAP B−A -0.00005.
- IC95% [-0.00572, +0.00550].
- Lead-level AP 0.3728 vs 0.3752.

**Interpretación:** Physical + Location es una representación mejor para explicar y gobernar el matching, pero no hay evidencia para venderla como mejora predictiva.

**Implicación:** usar la descomposición por claridad semántica y como base para interacciones, no porque E006 pruebe lift.

Interpretabilidad cluster por cluster: [INTERPRETABILIDAD](../matching_ab_v3/INTERPRETABILIDAD.md).

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D024 — Compatibility Routing tiene señal local, pero el A/B offline global sigue inconcluso

**Estado:** INCONCLUSIVE.

E007 mantuvo exactamente los mismos perfiles marginales y cambió sólo las interacciones:

- Persona×Need.
- Need×Physical.
- Need×Location.
- Need×Broker.
- Physical×Broker.
- Need×Physical×Broker.

Resultados:

- inquiry-level AP: 0.2098 → 0.2117.
- Lift@10%: 1.001x → 1.033x.
- Lead-level AP: 0.3752 → 0.4270.
- Lead-level AUC: 0.5469 → 0.5899.

Pero la comparación inferencial pre-registrada no separa los brazos:

- ΔAP +0.00205.
- IC95% [-0.00960, +0.01294].

**Interpretación:** hay una señal interesante a nivel Lead y en celdas específicas, pero no evidencia suficiente para un multiplicador global de Compatibility.

**Implicación:** convertir las mejores celdas en hipótesis de routing para un A/B online, no en reglas de producción.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D025 — La estructura relacional está limpia; Availability exige un join as-of

**Estado:** SUPPORTED.

La auditoría encontró 0 fallos críticos de PK/FK/cardinalidad y preservación de filas. Sin embargo, un join directo Inquiry×Availability por `spot_id` expande la tabla **10.02x**.

El pipeline correcto usa `latest snapshot_date <= inquiry_at`:

- cobertura global 92.38%;
- cobertura con lag <=90d 88.51%;
- snapshots futuros usados: 0.

**Interpretación:** la relación es 1:N temporal; Availability no se puede unir como una dimensión estática.

**Implicación:** cualquier feature de disponibilidad debe construirse con backward as-of y tests de no-futuro.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D026 — Modalidad es dura; sector y geografía son preferencias blandas

**Estado:** SUPPORTED.

En las 22,576 inquiries:

- modalidad Lead↔Spot compatible: **100.0%**;
- sector exacto: **70.35%**;
- municipio preferido exacto: **19.80%**;
- corredor exacto cuando se declara: **18.60%**.

El patrón es estable por search_sector.

**Interpretación:** el mercado observado respeta la modalidad, pero permite desviarse mucho de sector/localización preferida.

**Implicación:** municipio/corredor no deben convertirse en filtros duros. Son features de compatibilidad o penalizaciones suaves.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D027 — El Search Need debe poder actualizarse en T1

**Estado:** SUPPORTED.

Al cruzar Lead→Inquiry:

- 81.53% del requested rent budget cae dentro del rango inicial;
- 81.04% del requested sale budget cae dentro del rango inicial;
- mediana requested_area / target_area = **1.053x**;
- sólo **62.16%** de las inquiries queda entre 0.5x y 2x del target_area inicial.

**Interpretación:** la inquiry no sólo repite la necesidad declarada; la refina materialmente.

**Implicación:** mantener N1/N2/N3 como estado T0, pero recalcular/refinar Need en T1 con requested area/budget/urgency.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D028 — El missingness de presupuesto/precio es mayormente estructural por modalidad

**Estado:** SUPPORTED.

Condicionado a que el campo aplique:

- Lead min rent: 96.64% completo; max rent: 100%.
- Lead min sale: 96.40%; max sale: 100%.
- Spot rent/sale prices: 100% completos.

Además:

- 0 casos min_budget > max_budget.
- price_total ≈ price_sqm × area está dentro de 1% en **100%** de rent y sale listings comparables.

**Interpretación:** los nulls crudos de renta/venta no deben tratarse automáticamente como mala calidad; gran parte es missingness estructural por modalidad.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D029 — broker_response_hours no es un SLA limpio

**Estado:** NOT_SUPPORTED para interpretación directa como tiempo de respuesta.

El non-null rate de response_hours es ~85% en **todos** los outcomes, incluso `no_response`.

- 3,786 `no_response` tienen response_hours.
- 2,701 outcomes con respuesta no tienen response_hours.
- medianas por outcome son casi idénticas (~8.1–8.5h).

**Interpretación:** el nombre del campo no coincide con una semántica simple “horas hasta que respondió el broker”.

**Implicación:** no usarlo como driver causal/SLA sin definición de origen; las etiquetas B1/B2 basadas en rapidez se consideran low-trust.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D030 — Availability tiene coverage drift fuerte al inicio de la historia

**Estado:** SUPPORTED.

Cobertura backward-as-of:

- ene-2025 6.5%;
- jun-2025 84.7%;
- sep-2025 96.6%;
- dic-2025 99.9%;
- desde ene-2026 100%.

La consistencia interna sí es perfecta: available→days_until_available=0 y not_available→days_until_available>0 en 100%.

**Interpretación:** el dato es coherente cuando existe, pero su disponibilidad histórica cambia con el tiempo.

**Implicación:** monitorizar coverage/lag por cohorte y evitar interpretar missing availability temprano como “no disponible”.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D031 — Market Context todavía no es una feature histórica defendible

**Estado:** NOT_SUPPORTED para incorporación point-in-time actual.

Coverage exacta Spot geography × sector × inquiry month:

- global 23.84%;
- Industrial 26.76%;
- Land 19.73%;
- Office 22.34%;
- Retail 24.95%;
- julio-2026 0%.

Además no se conoce publication/effective time.

**Interpretación:** el problema no es sólo missingness; falta semántica temporal para saber qué contexto era realmente observable al scoring time.

**Implicación:** mantenerlo fuera del ABT hasta construir una tabla effective-dated o una regla de lag explícita.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D032 — Existen bolsillos locales de compatibilidad, no una regla global

**Estado:** INCONCLUSIVE.

Top celdas future-test, N>=50 y shrinkage hacia el baseline:

- N2×PH1×B6: N=73, 31.5% raw, 28.38% smooth, **1.37x**.
- N3×PH1×B5: N=81, **1.31x**.
- N3×LOC6: N=64, **1.29x**.
- PH3×B2: N=99, **1.28x**.
- PH3×B1: N=139, **1.26x**.
- N2×PH2×B3: N=67, **1.25x**.

**Interpretación:** la compatibilidad parece localizada en ciertos Need×Physical×Broker/Location, no como una mejora uniforme.

**Implicación:** priorizar estas celdas en un routing A/B randomizado; no multiplicar el score offline por el lift observado.

Interpretabilidad detallada: [INTERPRETABILIDAD](../matching_ab_v3/INTERPRETABILIDAD.md).

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D033 — spots.total_inquiries no equivale a la tabla de eventos

**Estado:** NOT_SUPPORTED para usarlo como historial de inquiries.

Al reconciliar `spots.total_inquiries` con el conteo real de `inquiries` por spot:

- exact match: 7.07%;
- total_inquiries >= event count: 37.43%;
- correlación: -0.051;
- diferencia mediana: -2.

**Interpretación:** total_inquiries probablemente representa otra ventana, definición o snapshot agregado.

**Implicación:** no usarlo como conteo de eventos histórico ni como feature point-in-time hasta aclarar su semántica.

Evidencia: [EV-010](../Evidencias/EV-010_matching_ab_v3.md).

## D034 — Rolling CV confirma ventaja de modelos tabulares sobre Multi-Head

**Estado:** SUPPORTED.

E006 repite E005 con cuatro folds forward-chaining por cohorte de lead:

- 7,980 snapshots OOF;
- 1,936 leads únicos;
- test cohorts disjuntos;
- bootstrap de 700 réplicas por lead.

Macro OOF:

- Specialist CatBoost: AP 0.4720, AUC 0.5820.
- Specialist RF: AP 0.4698, AUC 0.5711.
- pooled CatBoost + stage: AP 0.4665, AUC 0.5721.
- Multi-Head: AP 0.4498, AUC 0.5498.

Vs Multi-Head:

- Specialist CatBoost: ΔAP +0.0222, IC95% [+0.0068, +0.0361]; ΔAUC +0.0322, IC95% [+0.0197, +0.0461].
- Specialist RF: ΔAP +0.0201, IC95% [+0.0078, +0.0321].
- pooled CatBoost: ΔAP +0.0167, IC95% [+0.0016, +0.0315].

**Interpretación:** la conclusión de E005 ya no depende de un único holdout. El Multi-Head actual queda superado por varios challengers tabulares en múltiples cohortes temporales.

**Matiz:** Specialist CatBoost tiene el mejor macro AP puntual, pero la diferencia AP CatBoost−RF es pequeña y no robusta; no declarar un único ganador entre ambos sólo por ese ranking.

Evidencia: [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md).

## D035 — La trayectoria explícita aporta señal incremental en T2

**Estado:** SUPPORTED.

E007 mantiene exactamente los folds de E006 y añade sólo features point-in-time de trayectoria/progreso.

En T2:

- pooled CatBoost + trajectory vs pooled CatBoost: ΔAP +0.0161, IC95% [+0.0003, +0.0322], P(Δ>0)=97.9%; ΔAUC +0.0117, IC95% [+0.0004, +0.0237].
- Multi-Head + trajectory vs Multi-Head: ΔAP +0.0155, IC95% [+0.0013, +0.0303], P(Δ>0)=98.2%; ΔAUC +0.0176, IC95% [+0.0055, +0.0297].

Las variables incluyen gaps, velocidad de inquiries, respuestas pendientes/realizadas, tiempo desde aceptación, revisitas y cambios de restricciones, siempre as-of score time.

**Interpretación:** D014 deja de ser sólo una interpretación de feature importance: representar explícitamente progresión/estancamiento añade información predictiva fuera de muestra.

Evidencia: [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md).

## D036 — Trajectory features dependen de la arquitectura

**Estado:** NOT_SUPPORTED como mejora universal.

En T2:

- Random Forest + trajectory: ΔAP -0.0095, IC95% [-0.0191, -0.0002].
- Specialist CatBoost + trajectory: ΔAP -0.0101, IC95% [-0.0252, +0.0047].

En cambio, pooled CatBoost y Multi-Head sí mejoran de forma robusta.

**Interpretación:** las trajectory features son útiles como representación, pero no deben agregarse indiscriminadamente. En RF probablemente introducen redundancia/fragmentación de splits sobre señales ya capturadas por `interaction_history`.

**Implicación:** evaluar cualquier nuevo bloque de features contra la misma familia base, no transferirlo automáticamente entre algoritmos.

Evidencia: [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md).

## D037 — El meta-selector por etapa no es estable

**Estado:** INCONCLUSIVE como decisión de producción.

La familia elegida por validation cambia entre folds:

- E006 T0: ExtraTrees/LightGBM; T1: CatBoost/LightGBM; T2: pooled CatBoost/specialist CatBoost.
- E007 T0: CatBoost/pooled CatBoost/Multi-Head; T1: specialist/pooled CatBoost; T2: pooled CatBoost en 3/4 folds y specialist CatBoost en 1/4.

El híbrido tiene buenos puntos OOF, pero su composición depende del periodo.

**Interpretación:** no hay base suficiente para operar un router de modelos por etapa. La opción más defendible por simplicidad/evidencia es mantener un CatBoost fuerte como base dinámica y usar especialistas sólo donde un override tenga estabilidad temporal demostrada.

Evidencia: [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md), [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md).


## D038 — Persona debe separar adquisición de madurez conductual

**Estado:** PROPOSAL.

E008 reemplaza `persona_profile` por dos piezas explícitas:

- `acquisition_channel = leads.source`;
- `behavioral_profile` outcome-free con user type, company size, industry, prior searches/inquiries y conversión previa.

**Hipótesis:** reducir la mezcla semántica hará el perfil más interpretable y puede recuperar señal que el clustering de source estaba comprimiendo.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D039 — Need debe evolucionar de T0 a T1 sin volver a aprender calendario

**Estado:** PROPOSAL.

E009 crea `dynamic_need_profile` con requested area/budget, urgency, asked_visit, channel, message length y deltas contra el Need inicial. Excluye explícitamente weekday.

También añade `need_transition = Need_T0 -> Need_T1`.

**Hipótesis:** la actualización de necesidad al momento de inquiry mejorará ranking/lift frente al Need T0 estático.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D040 — Broker debe separarse en Supply y Service sin response_hours

**Estado:** PROPOSAL.

E010 sustituye el Broker legacy por:

- Broker Supply: mix de sector/modalidad/región, área y precios históricos;
- Broker Service: mix histórico de accepted/scheduled/rejected/no_response, asked_visit, urgency, message length y channel.

Todo queda congelado antes del profile cutoff y `broker_response_hours` se excluye por completo.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D041 — La siguiente compatibilidad debe ser jerárquica

**Estado:** PROPOSAL.

E011 prueba interacciones pre-especificadas:

`Dynamic Need -> Physical/Location -> Broker Supply/Service`

y compara tanto contra su padre marginal E010 como contra el E007 flat compatibility anterior.

Las celdas future-test se usarán sólo para descubrimiento, con N>=50 y shrinkage; no seleccionan el modelo.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).


## D042 — Dynamic Need debe aislarse del rediseño de Persona

**Estado:** PROPOSAL.

La primera escalera mostró que E008 Persona puede deteriorar el baseline. E012 vuelve a E006 y añade únicamente Dynamic Need + transición T0→T1.

**Objetivo:** saber si la señal dinámica era buena pero estaba siendo enmascarada por un cambio previo perjudicial.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D043 — Broker necesita un gate duro de balance

**Estado:** PROPOSAL.

El primer Broker Supply puede colapsar en un cluster dominante. E013 comprime la representación a especialización dominante, entropías/diversidad y escalas robustas winsorizadas.

El experimento **falla** si el cluster seleccionado no cumple min share >=5% y max share <=65%.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D044 — La jerarquía debe probarse sólo sobre la rama fuerte

**Estado:** PROPOSAL.

E014 añade compatibilidades sólo después de E012 Dynamic Need y E013 Broker balanceado. Se compara contra su padre y contra E007 old compatibility sobre el mismo future test.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).
