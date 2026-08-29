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
| D013 | SUPPORTED | Un Random Forest especializado en T2 supera ligeramente al head T2 actual; la superioridad del multi-head frente a especialistas no lineales queda abierta. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D014 | SUPPORTED | La señal T2 se interpreta mejor como trayectoria/progreso vs estancamiento que como efecto de la inquiry actual aislada. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D015 | SUPPORTED | Condicionada al historial observable, la inquiry actual y el match Lead↔Spot aportan poca señal incremental promedio en T2, aunque recuperan valor en el último T2. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D016 | INCONCLUSIVE | `availability_snapshot_age_days` aparece predictiva, pero su dirección es sospechosa y puede estar capturando estructura temporal/cobertura en lugar de disponibilidad accionable. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D017 | SUPPORTED | La baja concordancia entre rankings del multi-head y RF indica que las conclusiones más robustas son por familias, no por ranking exacto de variables individuales. | [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md) |
| D018 | PROPOSAL | La superioridad arquitectónica del multi-head frente a especialistas tabulares fuertes sigue abierta y requiere un benchmark equivalente multi-etapa. | [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md) |

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


## D013 — El multi-head todavía no gana contra especialistas no lineales

**Estado:** SUPPORTED para la comparación T2 disponible.

En el mismo test temporal T2:

- Multi-head T2: ROC AUC 0.595, AP 0.515, Lift@10% 1.39x.
- Random Forest T2: ROC AUC 0.609, AP 0.524, Lift@10% 1.43x.

**Interpretación:** D003 sigue siendo válido frente al challenger pooled y las regresiones separadas, pero no debe generalizarse a “multi-head es la mejor familia”. Un especialista tabular no lineal ya produjo una mejora pequeña.

**No demuestra:** que Random Forest sea definitivamente superior; fue un diagnóstico T2, no un benchmark exhaustivo multi-etapa.

**Siguiente implicación:** comparar el mismo multi-head contra especialistas RF/ExtraTrees/CatBoost y un pooled tabular bajo idéntico split, target, features y calibración.

Evidencia: [EV-004](../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md).

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

## D018 — Benchmark arquitectónico fuerte pendiente

**Estado:** PROPOSAL.

D003 mostró que el multi-head supera al pooled neural y a regresiones separadas, pero D013 encontró que un Random Forest T2 ya supera ligeramente al head T2.

**Pregunta abierta:** ¿la ventaja del multi-head se mantiene frente a especialistas tabulares fuertes y frente a un pooled CatBoost con stage como variable, manteniendo idénticos target, población, features y split?

**Experimento diseñado:** E005 compara Multi-Head, pooled NN, regresión separada, Random Forest, ExtraTrees, LightGBM, CatBoost especializado, CatBoost pooled y un híbrido elegido sólo con validation.

**Criterio:** la decisión primaria será macro Average Precision con IC95% bootstrap por lead.

Evidencia / experimento: [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md).
