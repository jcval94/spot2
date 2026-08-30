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
| D008 | PROPOSAL | El LLM de triage sigue siendo una visión de producto plausible, pero no se selecciona como uso principal del assessment porque falta raw inquiry text para evaluarlo honestamente. | [EV-008](../Evidencias/EV-008_llm_triage.md) |
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
| D038 | NOT_SUPPORTED | Behavioral Persona queda más limpia semánticamente, pero sustituir Persona por source+BP empeora AP y Lift@10; no se recomienda como reemplazo del scoring. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D039 | INCONCLUSIVE | Dynamic Need T1 es estable e interpretable y mejora lift/recall en punto, pero el delta AP global sigue cruzando cero. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D040 | NOT_SUPPORTED | El primer Broker clean no mejora lift y su componente Supply colapsa 98.3% de brokers en un cluster. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D041 | INCONCLUSIVE | La primera jerarquía eleva métricas lead-level en punto, pero no supera robustamente a E007 y pierde AUC/AP global. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D042 | INCONCLUSIVE | Dynamic Need aislado sobre E006 sube Lift@10 a 1.108x y Recall@20 a 21.96%, pero AP +0.0013 no es robusto. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D043 | SUPPORTED | Broker Supply no forma clusters balanceados bajo dos representaciones: 98.3% dominante en v1 y 70.3%/3.7% en la versión compacta. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D044 | NOT_SUPPORTED | E014 no es elegible como tratamiento porque su padre E013 falla el representation gate de Broker Supply. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D045 | INCONCLUSIVE | Broker Service BSV1–BSV3 sí es balanceado/estable (ARI 0.948), pero su ganancia marginal de AP es ~0 y el lift mejora sólo en punto. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D046 | INCONCLUSIVE | La jerarquía Dynamic Need×Physical/Location×Broker Service eleva Lift@10 a 1.172x, pero no mejora AP robustamente ni desplaza a E007 globalmente. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D047 | INCONCLUSIVE | DN4×LOC1×BSV1 establece un nuevo máximo local: 1.510x lift suavizado (N=60), pero es exploratorio y sujeto a multiple testing. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D048 | SUPPORTED | La transición Need T0→T1 es asimétrica: N1/renta permanece DN1 en 99.8%, mientras N2/N3 se fragmentan en regímenes de presupuesto/área. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D049 | NOT_SUPPORTED | Ningún stack nuevo demuestra ser reemplazo global de E007: mejora lift puntual, pero E007 conserva el mejor AP y ranking lead-level sin delta robusto en contra. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D050 | PROPOSAL | El mejor uso LLM actualmente justificable es auditar consistencia semántica entre el copy de listings y sus atributos estructurados; debe superar un baseline Rules-only antes de integrarse al negocio. | [EV-014](../Evidencias/EV-014_llm_inventory_quality.md) |
| D051 | SUPPORTED | El copy sintético es extremadamente templated (12 oraciones únicas; 84.4% de filas reutilizan descripción exacta) y Rules-only ya marca 322/3,000 spots como candidatos, por lo que el LLM enfrenta un baseline fuerte. | [EV-015](../Evidencias/EV-015_llm_inventory_semantic_audit.md) |
| D052 | SUPPORTED | El future test de matching ya fue consumido para discovery iterativo; puede reproducir resultados registrados, pero no confirmar nuevas celdas descubiertas después. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D053 | SUPPORTED | La arquitectura de segmentación decision-ready es Persona actual + Need T0 + Dynamic Need T1 + Physical + Location + Broker legacy, con Broker Service auxiliar y sin Broker Supply/Inquiry Intent. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D054 | SUPPORTED | En esta línea el cuello de botella dejó de ser el algoritmo de clustering: múltiples clusterers/K no producen lift global robusto; la ganancia útil vino de separar conceptos y estados T0→T1. | [EV-006](../Evidencias/EV-006_profile_clustering_v2.md), [EV-010](../Evidencias/EV-010_matching_ab_v3.md), [EV-013](../Evidencias/EV-013_matching_profiles_v4.md) |
| D055 | SUPPORTED | La revisión semántica cross-field revela un patrón material Land × lenguaje de edificio/interiores: 230 casos, 182 incrementales sobre Rules v1; esto justifica semantic rule discovery, no superioridad del LLM. | [EV-015](../Evidencias/EV-015_llm_inventory_semantic_audit.md) |
| D056 | SUPPORTED | El ABT canónico debe distinguir missing estructural, estado mutable y eventos point-in-time: rent/sale N/A no debe median-imputarse; current Spot state se reconstruye o bloquea; 673 scheduled_visit sin response time requieren label ambiguity en vez de falso negativo. | [EV-016](../Evidencias/EV-016_abt_feature_engineering.md) |
| D057 | PROPOSAL | El LLM no se justifica como tratamiento general de las 86 variables. Sus candidatos defendibles son semantic QA sobre title/description y, si existiera raw inquiry text, extracción estructurada de intención/flexibilidad/restricciones. | [EV-016](../Evidencias/EV-016_abt_feature_engineering.md), [EV-015](../Evidencias/EV-015_llm_inventory_semantic_audit.md) |
| D060 | SUPPORTED | El proceso presenta drift temporal fuerte: las interacciones se comprimen hacia el alta del lead y rolling CV confirma non-stationarity. | [EV-020](../Evidencias/EV-020_eda_profundo.md), [EV-021](../Evidencias/EV-021_temporal_drift_stress.md) |
| D061 | SUPPORTED | El dataset contiene clipping y redundancias sintéticas fuertes en área, presupuesto y precios de Spot. | [EV-020](../Evidencias/EV-020_eda_profundo.md) |
| D062 | SUPPORTED | Rareza multivariable no equivale a error ni oportunidad; no hay base para borrar outliers automáticamente. | [EV-020](../Evidencias/EV-020_eda_profundo.md), [EV-024](../Evidencias/EV-024_outlier_handling.md) |
| D063 | SUPPORTED | Market Context sigue bloqueado para histórico hasta disponer de semántica de publicación/effective time. | [EV-020](../Evidencias/EV-020_eda_profundo.md) |
| D064 | SUPPORTED | Availability tiene estado y frescura; snapshot age es guardrail/staleness, no señal comercial demostrada. | [EV-020](../Evidencias/EV-020_eda_profundo.md), [EV-023](../Evidencias/EV-023_availability_staleness.md) |
| D065 | INCONCLUSIVE | scheduled_visit está débilmente acoplado a compatibilidad intuitiva; limita lo que el proxy demuestra sobre matching real. | [EV-020](../Evidencias/EV-020_eda_profundo.md) |
| D066 | SUPPORTED | Current-state aggregates de Spot no son snapshots históricos coherentes y deben seguir bloqueados en scoring retrospectivo. | [EV-020](../Evidencias/EV-020_eda_profundo.md) |
| D067 | SUPPORTED | prior_searches y prior_inquiries no son equivalentes; deben evaluarse por ablación separada. | [EV-020](../Evidencias/EV-020_eda_profundo.md) |
| D068 | INCONCLUSIVE | La dispersión bruta de broker justifica prueba histórica, no interpretación causal. | [EV-020](../Evidencias/EV-020_eda_profundo.md) |
| D069 | SUPPORTED | La aparente fortaleza T1 del RF depende materialmente de clocks/progreso inestables; E005/T1 raw queda bloqueado para producción. | [EV-022](../Evidencias/EV-022_temporal_feature_ablation.md) |
| D070 | SUPPORTED | Availability freshness debe tratarse como guardrail; raw snapshot age no justifica ventaja predictiva robusta. | [EV-023](../Evidencias/EV-023_availability_staleness.md) |
| D071 | NOT_SUPPORTED | Eliminar anomalies de entrenamiento no mejora de forma robusta; no se adopta limpieza automática por Isolation Forest. | [EV-024](../Evidencias/EV-024_outlier_handling.md) |
| D072 | INCONCLUSIVE | Price totals son redundantes por construcción, pero la no-inferioridad predictiva de retirarlos no quedó demostrada bajo el margen pre-registrado. | [EV-025](../Evidencias/EV-025_redundancy_ablation.md) |
| D073 | SUPPORTED | prior_searches deteriora el RF en este split y debe retirarse del release candidate; prior_inquiries no demuestra el mismo patrón. | [EV-026](../Evidencias/EV-026_prior_history_ablation.md) |
| D074 | INCONCLUSIVE | El prior histórico de broker no entrega lift robusto y queda fuera del release/routing. | [EV-027](../Evidencias/EV-027_broker_prior_point_in_time.md) |
| D075 | SUPPORTED | E028 tiene protocolo definitivo y E029 artifact congelado, pero launch sigue bloqueado hasta prospective gate + A/A productivo. | [EV-028](../Evidencias/EV-028_definitive_abt_target.md), [EV-029](../Evidencias/EV-029_drift_sanitized_release_candidate.md) |
| D076 | SUPPORTED | Un scheduled_visit con event time desconocido no puede imputarse a negativo; debe ser AMBIGUOUS y producción exige timestamp real. | [EV-028](../Evidencias/EV-028_definitive_abt_target.md) |
| D077 | PROPOSAL | La evaluación causal definitiva debe ser lead-level, ITT y medir el sistema completo durante 30 días, no snapshots/inquiries aisladas. | [EV-028](../Evidencias/EV-028_definitive_abt_target.md) |
| D078 | SUPPORTED | El release candidate debe validarse en cohorte genuinamente post-freeze; el histórico post-selección no puede servir como confirmación. | [EV-029](../Evidencias/EV-029_drift_sanitized_release_candidate.md) |
| D079 | SUPPORTED | E030 materializa una ABT canónica y validada a nivel lead×stage×score_time, preservando ambiguous/censoring y separando model features de guardrails/audit-only. | [EV-030](../Evidencias/EV-030_definitive_abt.md) |
| D080 | NOT_SUPPORTED | T0 no recupera señal útil con scale/specificity, semantic Need ni soft clusters bajo la target E028; el mejor challenger permanece cerca/debajo de azar. | [EV-031](../Evidencias/EV-031_semantic_feature_engineering_ladder.md), [EV-032](../Evidencias/EV-032_t0_semantic_recovery.md) |
| D081 | NOT_SUPPORTED | T1 tampoco se recupera con Dynamic Need + PH/LOC + semantic interactions; el challenger reduce AUC de forma robusta vs atomic baseline. | [EV-031](../Evidencias/EV-031_semantic_feature_engineering_ladder.md), [EV-033](../Evidencias/EV-033_t1_semantic_recovery.md) |
| D082 | SUPPORTED | Los clusters semánticos pueden seguir siendo útiles para interpretación/routing, pero no deben promoverse automáticamente a LeadQuality bajo la target canónica. | [EV-013](../Evidencias/EV-013_matching_profiles_v4.md), [EV-033](../Evidencias/EV-033_t1_semantic_recovery.md) |
| D083 | SUPPORTED | El test E030 quedó consumido por E032/E033; nuevas familias de FE son desarrollo y requieren nueva cohorte para confirmación independiente. | [EV-032](../Evidencias/EV-032_t0_semantic_recovery.md), [EV-033](../Evidencias/EV-033_t1_semantic_recovery.md), [EV-034](../Evidencias/EV-034_general_feature_engineering_catalog.md) |
| D084 | NOT_SUPPORTED | Una segunda ola outcome-free (missingness, frequency, bins, geo/inventory relative) tampoco recupera T0; no existe señal dev estable con los campos actuales. | [EV-035](../Evidencias/EV-035_advanced_feature_engineering.md) |
| D085 | NOT_SUPPORTED | La pista T1 geo/inventory de E035 no se sostiene al aislarla: E036 no obtiene AUC >0.50 en ningún fold para ninguna variante. | [EV-035](../Evidencias/EV-035_advanced_feature_engineering.md), [EV-036](../Evidencias/EV-036_t1_geo_inventory_decomposition.md) |
| D086 | INCONCLUSIVE | Priors categóricos target-encoded estrictamente temporales mejoran levemente T1 en AUC/AP, pero no Lift@10 ni estabilidad suficiente; no activan LeadQuality. | [EV-037](../Evidencias/EV-037_temporal_smoothed_categorical_priors.md) |
| D087 | SUPPORTED | Neutralidad debe aplicarse al head LeadQuality, no a toda la etapa: T0/T1 mantienen capas semánticas/routing aunque su propensity head quede neutral. | [EV-038](../Evidencias/EV-038_stage_aware_feature_policy.md) |
| D088 | SUPPORTED | Con E031–E037, seguir recombinando los mismos campos aumenta research-overfitting; reabrir T0/T1 requiere nueva fuente, target o cohorte independiente. | [EV-038](../Evidencias/EV-038_stage_aware_feature_policy.md) |
| D089 | SUPPORTED | El paquete actual no contiene raw inquiry text; sólo message_length y campos estructurados, por lo que un LLM semántico de inquiry no puede evaluarse honestamente hoy. | [EV-039](../Evidencias/EV-039_llm_semantic_inquiry_features.md) |
| D090 | PROPOSAL | Si se incorpora texto real, el LLM debe extraer semántica estructurada (intent, constraints, readiness, compatibility, trajectory), no una probabilidad directa de conversión. | [EV-039](../Evidencias/EV-039_llm_semantic_inquiry_features.md) |
| D091 | SUPPORTED | La línea T0/T1 queda CLOSED/DECISION-READY con los datos actuales; reabrir requiere nueva información, target, temporalidad o cohorte, no más combinaciones del mismo histórico. | [EV-040](../Evidencias/EV-040_feature_engineering_closure.md) |

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

**Decisión posterior:** conservar esta idea como Product Vision, no como implementación principal. La reevaluación del uso obligatorio de IA está documentada en [registro_flujo/llm_use_case](../registro_flujo/llm_use_case/) y conduce a D050 como caso actualmente preferido.

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


## D038 — Behavioral Persona mejora la semántica, no el scoring

**Estado:** NOT_SUPPORTED como reemplazo predictivo.

E008 excluyó `source` del clustering y separó explícitamente canal de adquisición de madurez conductual. El resultado es interpretable y estable:

- BP1: baja historia / mainstream.
- BP2: manufacturing con baja historia.
- BP3: alta madurez; prior inquiries altas y 85% con conversión previa.
- GMM K=3, ARI=1.000, shares 59.0% / 26.3% / 14.8%.

Sin embargo, frente a E006:

- AP 0.2098 → 0.2027.
- ΔAP -0.0071, IC95% [-0.0150,+0.0004].
- Lift@10 1.001x → 0.937x.

**Interpretación:** la nueva BP es mejor para explicar madurez, pero pierde información útil del `persona_profile` actual para ranking. Conservarla como dimensión explicativa; no reemplazar el scoring.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D039 — Dynamic Need T1 es la nueva segmentación más informativa del Lead

**Estado:** INCONCLUSIVE para mejora global; fuerte para representación.

Dynamic Need excluye weekday y produce 5 perfiles con silhouette 0.620, ARI=1.000 y shares 65.0% / 12.9% / 11.5% / 5.4% / 5.3%.

- DN1: renta mainstream.
- DN2: venta / presupuesto alto.
- DN3: venta value + expansión moderada de área.
- DN4: **stretch-space**: mucho más espacio solicitado con presupuesto bajo.
- DN5: premium-budget + reducción de área.

Sobre la rama contaminada por E008, E009 recupera lift. Por eso el efecto se aisló posteriormente en E012.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D040 — El primer Broker limpio no funciona como reemplazo

**Estado:** NOT_SUPPORTED.

E010 eliminó `broker_response_hours`, pero:

- Broker Supply v1 concentra **98.3%** en BS1.
- Lift@10 cae de 1.033x a 0.948x frente a E009.
- ΔAP +0.00049 con IC95% [-0.00686,+0.00843].

**Interpretación:** quitar una variable problemática no basta; Supply disponible está demasiado dominado por un régimen común y los perfiles conjuntos no mejoran ranking.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D041 — La primera jerarquía no supera al flat compatibility

**Estado:** INCONCLUSIVE.

E011 añadió interacciones sobre BP + Dynamic Need + Physical/Location + Broker Supply/Service.

Vs E010:
- ΔAP -0.00018, IC95% [-0.01113,+0.01151].
- ΔLift@10 +0.064, IC95% [-0.119,+0.245].

Vs E007:
- ΔAP -0.00460, IC95% [-0.0224,+0.0126].
- ΔLift@10 -0.024.

Lead-level AP sube a 0.4198, pero E007 sigue en 0.4270.

**Conclusión:** la idea jerárquica sigue siendo razonable, pero esta implementación no es un nuevo ganador.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D042 — Dynamic Need aislado mejora la concentración del top

**Estado:** INCONCLUSIVE.

E012 vuelve al baseline fuerte E006 y añade únicamente Dynamic Need + transición T0→T1.

Resultados:

- AP 0.20981 → **0.21135**.
- Lift@10 1.001x → **1.108x**.
- Recall@20 19.72% → **21.96%**.
- ΔAP +0.00131, IC95% [-0.00690,+0.00881].
- ΔLift@10 +0.0993, IC95% [-0.0753,+0.2706].
- P(ΔRecall@20>0)=97.25%, aunque el IC95% toca prácticamente cero.

**Interpretación:** Dynamic Need merece conservarse como challenger T1 y para routing, pero todavía no hay evidencia para declarar mejora global robusta.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D043 — Broker Supply no debe forzarse a clusters

**Estado:** SUPPORTED.

Se probaron dos representaciones outcome-free:

1. Supply v1: 98.3% / 1.3% / 0.3%.
2. Supply compact/winsorized: **70.3% / 26.0% / 3.7%**, ARI 0.949.

La segunda sigue violando el gate pre-registrado min>=5% y max<=65%.

**Interpretación:** la falta de balance no es un simple problema de algoritmo ni de outliers. Con la información actual, Supply no sostiene arquetipos discretos suficientemente diferenciados.

**Implicación:** usar descriptores continuos/directos de Supply o enriquecer los datos; no seguir moviendo K hasta fabricar balance.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D044 — E014 queda invalidado por dependencia de un perfil no elegible

**Estado:** NOT_SUPPORTED.

E014 dependía de E013, que requería **ambos** perfiles Broker balanceados. Broker Supply falló el gate, por lo que E013 y E014 no fueron científicamente elegibles como tratamientos.

Sus archivos de resultados conservan métricas copiadas del padre sólo para registrar el harness immutable; **no representan una ejecución de tratamiento**.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D045 — Broker Service sí es un perfil defendible, pero no mejora globalmente por sí solo

**Estado:** INCONCLUSIVE.

BSV:
- Bisecting K=3.
- shares 57.7% / 23.7% / 18.7%.
- ARI **0.948**.

Interpretación:
- BSV1: servicio diversificado / mayor actividad.
- BSV2: acceptance-heavy / menor volumen.
- BSV3: mayor urgencia y mayor scheduled_visit histórico.

E015 vs E012:
- AP prácticamente idéntico: 0.211347 vs 0.211344.
- ΔAP -0.00002, IC95% [-0.00062,+0.00059].
- Lift@10 1.108x → 1.118x.

**Conclusión:** BSV es una buena segmentación descriptiva y una dimensión útil de interacción, pero no un driver marginal global demostrado.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D046 — La jerarquía de Service mejora lift puntual, no AP global

**Estado:** INCONCLUSIVE.

E016 añade Dynamic Need × Physical/Location × Broker Service sobre E015.

- AP 0.21068.
- Lift@10 **1.172x**.
- Lead AP 0.4049.
- Lead AUC 0.5730.
- Lead Lift@10 **1.365x**.

Vs E015:
- ΔAP +0.00005, IC95% [-0.01072,+0.01108].
- ΔLift@10 +0.0499, IC95% [-0.1548,+0.2474].

Vs E007:
- ΔAP -0.00097, IC95% [-0.01650,+0.01471].
- ΔLift@10 +0.137, IC95% [-0.091,+0.370].

**Interpretación:** concentra mejor positivos en el top en punto, pero paga con AUC/recall y no desplaza robustamente a E007.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D047 — DN4 × LOC1 × BSV1 es el mayor pocket local encontrado

**Estado:** INCONCLUSIVE.

Future test, N>=50 y shrinkage:

- combinación: **DN4 × LOC1 × BSV1**;
- N=60;
- scheduled_visit raw **36.67%**;
- smoothed **31.37%**;
- lift suavizado **1.510x**;
- Wilson lower rate / baseline **1.234x**.

Interpretación:
- DN4 = stretch-space, mucho más espacio con presupuesto bajo;
- LOC1 = centro metropolitano CDMX–Naucalpan;
- BSV1 = Broker Service diversificado/de mayor actividad.

Supera el récord previo EV-010 (1.366x) y la primera pasada v4 DN4×BV1 (1.427x).

**No prueba:** causalidad, family-wise significance ni estabilidad temporal independiente. La celda fue descubierta al inspeccionar múltiples combinaciones del future test.

**Implicación:** candidata #1 para réplica/online routing A/B; no multiplicar el score por 1.51.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D048 — La actualización T0→T1 es especialmente valiosa para venta/flexible

**Estado:** SUPPORTED.

Matriz future:

- N1/renta → DN1: **99.82%**.
- N2/venta se divide entre DN1 33.3%, DN2 26.5%, DN3 23.8%, DN4 9.2%, DN5 7.2%.
- N3/both se divide entre DN1 36.2%, DN2 23.3%, DN3 20.7%, DN4 11.7%, DN5 8.1%.

**Interpretación:** la inquiry aporta poca reclasificación a renta, pero mucha resolución adicional para venta y flexible. El valor de Dynamic Need no es homogéneo por Need T0.

**Implicación:** priorizar actualización T1 especialmente para N2/N3; N1 puede tratarse como estado más estable.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D049 — No hay un nuevo reemplazo global de E007

**Estado:** NOT_SUPPORTED para la hipótesis de un nuevo ganador universal.

Comparación de puntos:

- E007: AP **0.21171**, Lead AP **0.4270**, Lead AUC **0.5899**.
- E012: AP 0.21135, Lift@10 **1.108x**.
- E015: AP 0.21134, Lift@10 **1.118x**.
- E016: AP 0.21068, Lift@10 **1.172x**, Lead AP 0.4049.

Los nuevos modelos mejoran concentración top-decile en punto, pero los deltas de AP/lift tienen intervalos que cruzan cero.

**Conclusión:** no sustituir E007 sólo por lift@10. Conservar Dynamic Need/BSV como features y hypotheses de routing; decidir un cambio global únicamente con nueva validación temporal u online.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).



## D050 — El mejor uso LLM actual es auditar la calidad semántica del inventario

**Estado:** PROPOSAL.

La reevaluación del caso de uso de IA descartó como **uso principal por diseño, no por resultado experimental**, dos rutas:

- Broker Copilot / triage: no existe raw inquiry text para demostrar la parte semántica con los datos del candidato;
- LLM-assisted fallback reranking/explanation: sector, modalidad, presupuesto, área, ubicación y disponibilidad son mayormente estructurados, por lo que un ranking determinístico y templates pueden resolver gran parte del problema sin un LLM.

En cambio, `spots.title` y `spots.description` sí contienen lenguaje libre. Un spot-check manual detectó casos candidatos donde el copy y `spot_attributes` entran en conflicto, por ejemplo claims de iluminación natural frente a `natural_light=false` o claims de seguridad 24/7 frente a `security_type=none`.

**Hipótesis:** un LLM puede normalizar paráfrasis y detectar inconsistencias semánticas adicionales a un baseline Rules-only.

**Baseline obligatorio:** reglas explícitas de alta precisión.

**Evaluación obligatoria:** labels humanos; comparar Rules-only vs LLM-only vs Rules+LLM en precision, recall, F1, falsos positivos y cobertura incremental.

**No demuestra todavía:** que el LLM sea superior a reglas, que el texto sea la fuente correcta cuando existe conflicto, ni que los flags deban modificar automáticamente el Lead Opportunity Score.

**Siguiente implicación:** implementar `E015_llm_inventory_semantic_audit` con OpenAI Responses API directa, output estructurado y una cola de Catalog QA como primera integración potencial.

Evidencia: [EV-014](../Evidencias/EV-014_llm_inventory_quality.md).  
Evolución de la decisión: [registro_flujo/llm_use_case](../registro_flujo/llm_use_case/).


## D051 — El copy sintético hace de Rules-only un baseline fuerte

**Estado:** SUPPORTED.

E015 ejecutó el perfilado completo de `spots.description` sobre 3,000 listings:

- 856 descripciones exactas únicas;
- sólo 28.5% de unicidad exacta;
- 84.37% de los listings comparten su descripción exacta con al menos otro;
- únicamente 12 oraciones distintas componen todas las descripciones.

El baseline inicial de cuatro familias de claims detecta **330 conflictos candidatos en 322 spots únicos (10.73%)**:

- natural_light: 153;
- readiness: 101;
- security: 55;
- parking: 21.

**Interpretación:** la dificultad del experimento no es demostrar que un LLM puede leer el copy. Con sólo 12 oraciones, reglas explícitas pueden cubrir gran parte del lenguaje observado. Para justificar el LLM debe existir **cobertura incremental accionable** sobre Rules-only.

**No demuestra:** que los 322 spots sean errores confirmados, que el texto sea la fuente correcta, ni que las reglas tengan precision alta. Esos puntos requieren gold labels humanos.

**Siguiente implicación:** congelar la muestra humana de 200 listings y evaluar Rules-only vs LLM-only vs Rules+LLM antes de cualquier integración al fallback o Lead Opportunity Score.

Evidencia: [EV-015](../Evidencias/EV-015_llm_inventory_semantic_audit.md).


## D052 — El future test de matching ya no es un holdout confirmatorio para nuevas celdas

**Estado:** SUPPORTED como restricción metodológica.

El mismo future test de 4,516 inquiries / 2,065 Leads fue usado secuencialmente para:

- E006/E007;
- inspección de compatibility cells;
- diseño de las hipótesis v4;
- E008–E016;
- nueva inspección de celdas, incluyendo DN4×LOC1×BSV1.

**Interpretación:** la temporalidad de cada evaluación sigue siendo correcta, pero la muestra ya influyó en decisiones posteriores. Por tanto, una nueva celda encontrada ahora no puede validarse de forma independiente sobre ese mismo conjunto.

**Implicación:** el test queda congelado para reproducibilidad. La confirmación de nuevos pockets exige nueva cohorte temporal o A/B online.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).

## D053 — La arquitectura final de segmentación queda congelada

**Estado:** SUPPORTED / DECISION-READY.

La síntesis de EV-006, EV-010 y EV-013 deja como representación recomendada:

- Persona actual P1–P7 como acquisition/history feature de referencia;
- Search Need T0 N1–N3;
- Dynamic Need T1 DN1–DN5;
- Physical PH1–PH4;
- Location LOC1–LOC7;
- Broker legacy para benchmark global;
- Broker Service BSV1–BSV3 como faceta auxiliar/experimental;
- Availability backward-as-of.

Se excluyen:

- Inquiry Intent weekday;
- Behavioral Persona BP como reemplazo del scoring;
- Broker Supply clusters;
- Market Context histórico actual;
- response_hours como SLA;
- total_inquiries como event history.

**Ranking:** E007 permanece como referencia global; E012/E016 son challengers orientados a lift/routing.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).  
Decisión: [DECISION_SEGMENTACION](../matching_profiles_v4/DECISION_SEGMENTACION.md).

## D054 — Seguir buscando otro clustering ya no es la palanca principal

**Estado:** SUPPORTED.

A lo largo de la línea se probaron múltiples métodos y K, con selección outcome-free, balance y estabilidad. Cambiar algoritmo produjo perfiles más o menos balanceados, pero no una mejora global robusta de ranking.

Los avances más útiles provinieron de **redefinir el concepto**:

- separar Persona de Need;
- separar Spot Physical de Location;
- actualizar Need T0→T1;
- separar Broker Service de Supply;
- rechazar familias que sólo codificaban weekday o colapsaban.

**Interpretación:** el cuello de botella ya no es “K-Means vs GMM vs Bisecting”, sino qué estado/faceta de negocio merece representarse y con qué información point-in-time.

**Implicación:** cerrar búsqueda general de clusterer/K en esta línea. Nuevas iteraciones deben aportar nueva semántica, nueva fuente o nueva validación, no sólo otro algoritmo.

Evidencia: [EV-006](../Evidencias/EV-006_profile_clustering_v2.md), [EV-010](../Evidencias/EV-010_matching_ab_v3.md), [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).


## D055 — La semántica cross-field descubre un patrón material Land × building copy

**Estado:** SUPPORTED como hallazgo de data quality; no como benchmark de un modelo LLM.

La revisión semántica posterior a Rules v1 identificó un tipo de inconsistencia no representado por comparaciones uno-a-uno:

```text
sector_name = Land
+
lenguaje de edificio/interiores
```

Ejemplos del lenguaje: “buena iluminación natural”, “recién remodelado”, “acabados modernos”, “listo para ocupar” y “acabados de primera”.

Sobre 3,000 spots:

- S001 aparece en 230 listings Land;
- 182 de ellos no eran positivos en Rules v1;
- Rules v1 marca 322 spots únicos;
- Rules v2 post-discovery marca 504;
- incremento atribuible a S001: 182 spots, 6.07% del inventario.

**Interpretación:** el valor diferencial de un LLM en este dataset es más defendible como **semantic rule discovery / long-tail anomaly discovery** que como endpoint permanente para repetir verificaciones sobre copy altamente templated.

**No demuestra:** que esos 230 sean errores confirmados, que Rules v2 tenga precision alta ni que un LLM supere Rules-only. La muestra original fue inspeccionada durante discovery y no puede servir como holdout limpio para S001.

**Corrección metodológica:** final evaluation pasa a un holdout disjunto de 240 listings y un challenge set Land de 100 filas para precision del patrón.

Evidencia: [EV-015](../Evidencias/EV-015_llm_inventory_semantic_audit.md).


## D056 — El tratamiento correcto de variables es parte del modelo

**Estado:** SUPPORTED.

La auditoría de las 86 columnas muestra que un preprocesamiento genérico no es suficiente para Spot2. E016 formaliza un contrato por variable y etapa:

- missing de renta/venta es mayormente **estructural por modalidad**, no un NaN intercambiable;
- `lead_score_internal` permanece bloqueado;
- `days_on_market`, `total_inquiries`, `total_views` e `is_active` no entran como current-state historical features;
- `days_on_market` se sustituye por `score_time - spot.created_at`;
- `total_inquiries` se sustituye por historia de inquiries as-of;
- `broker_id` se usa como llave para perfil histórico, no como identificador memorizable;
- Availability se une únicamente backward-as-of;
- atributos built-environment se gatean para Land en vez de permitir que valores sintéticos físicamente extraños dominen la representación.

Además, `broker_response_hours` no sólo tiene missingness: su semántica es inconsistente. Hay **673 scheduled_visit sin response time**. Para un target de 30 días no se puede demostrar si esos outcomes ocurrieron dentro del horizonte. E016 marca esos labels como temporalmente ambiguos y excluye las filas afectadas del ABT training-ready.

**Interpretación:** data treatment, leakage y target observability forman parte de la especificación estadística del modelo; no son limpieza cosmética.

**No demuestra:** que E016 mejore métricas predictivas. El benchmark temporal sobre estos ABTs es el siguiente experimento.

Evidencia: [EV-016](../Evidencias/EV-016_abt_feature_engineering.md).

## D057 — El LLM tiene una frontera clara dentro del Feature Engineering

**Estado:** PROPOSAL.

La revisión variable-por-variable no justifica aplicar un LLM a precios, presupuestos, áreas, geografía, enums, availability ni response timing. Esos problemas son determinísticos, temporales o de unidades.

Los usos defendibles son:

1. **`spots.title + spots.description`**: semantic/cross-field QA, detección de contradicciones y extracción de claims;
2. **raw inquiry text futuro**: intent stage, flexibilidad de ubicación/área/presupuesto, must-have constraints, completeness y confidence.

Con los datos actuales, `message_length` no contiene el texto y por tanto no permite extraer semántica honestamente.

Para inventario, el LLM debe continuar como challenger incremental sobre Rules, no como sustituto automático de atributos estructurados. Una contradicción genera una señal de QA; no autoriza al modelo a reescribir el dato.

**Implicación:** el primer benchmark posterior a E016 debe mantener ABT base sin LLM y probar por ablación `Rules semantic flags` y luego `LLM incremental flags`, sólo si existe un output versionado y reproducible.

Evidencia: [EV-016](../Evidencias/EV-016_abt_feature_engineering.md), [EV-015](../Evidencias/EV-015_llm_inventory_semantic_audit.md).


## D060 — El drift temporal no es un detalle; cambia la pregunta predictiva

**Estado:** SUPPORTED descriptivamente; su impacto predictivo se somete a stress test en E021/E022.

**Qué se observó.** El número total de inquiries por lead permanece relativamente estable, aproximadamente 4.2–4.8, pero la distribución temporal cambia de forma radical. Las inquiries dentro de 30 días pasan de 1.37 por lead en 2025-01 a 4.42 en 2026-06 y la mediana de tiempo a primera inquiry cae de 7.82 a 2.31 días. En paralelo, el proxy lead-level a 30 días sube aproximadamente de 20.1% a 56.5%.

**Por qué esto importa.** El target usa un horizonte fijo de 30 días. Si el proceso sintético mueve las interacciones cada vez más cerca de la creación del lead, una proporción mayor de eventos cabe mecánicamente dentro de esa ventana. Un modelo puede entonces encontrar señal en `days_from_lead_creation`, `inquiry_number`, `days_since_first_inquiry`, mes o weekday aunque parte de esa señal represente **régimen/cohorte** y no una relación comercial estable.

Esto no es leakage clásico: las variables pueden conocerse correctamente al momento del score. El riesgo es diferente: **generalización bajo non-stationarity**. Un feature legal puede ser inestable.

**Qué no demuestra.** No demuestra que interactuar antes cause una visita ni que las variables temporales deban eliminarse. Tampoco permite cuantificar todavía cuánto desempeño depende de ellas.

**Qué lo resuelve.** E021 evalúa rolling future cohorts y PSI; E022 remueve clocks de calendario/progreso bajo el split congelado de E005 y compara con bootstrap por lead.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D061 — Hay reglas del generador dentro de features aparentemente continuas

**Estado:** SUPPORTED.

**Qué se observó.** Aproximadamente 35.53% de `requested_area/spot_area` se concentra en 0.30 y 21.37% en 5.00. Cerca de una cuarta parte de los presupuestos solicitados queda exactamente en el máximo declarado del lead. Además, `spot_price_total` es prácticamente `area × price_sqm`, con error relativo p99 casi nulo.

**Por qué importa.** Un modelo puede repartir importancia entre variables que son copias algebraicas o productos de clipping, inflando la sensación de evidencia independiente. En modelos de árboles esto puede no destruir desempeño, pero sí vuelve más frágil la interpretación y puede crear splits artificiales en los límites del generador.

**Qué no demuestra.** No implica que todas esas variables deban eliminarse; algunas transformaciones derivadas pueden ser útiles para matching.

**Qué lo resuelve.** E025 retira únicamente los price totals redundantes, manteniendo ratios de compatibilidad, y exige no-inferioridad fuera de tiempo.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D062 — Outlier no significa registro malo

**Estado:** SUPPORTED.

**Qué se observó.** El Isolation Forest outcome-free encuentra rareza multivariable dentro de sector × modalidad, pero los casos más anómalos no muestran mayor scheduled_visit. El top 1% tiene ~17.95% frente a ~19.94% en el resto; top 3% ~19.12% frente a ~19.94%.

**Por qué importa.** Las áreas, precios y capacidades de inmuebles viven en regímenes de escala muy distintos. Borrar una nave industrial enorme porque es extrema respecto a la nube general puede eliminar precisamente un submercado válido. Un detector de anomalías sirve como **lupa de QA**, no como regla automática de limpieza.

**Qué no demuestra.** El EDA no prueba que conservar todos los outliers sea óptimo para modelado.

**Qué lo resuelve.** E024 ajusta Isolation Forest sólo sobre train, excluye clocks temporales, elimina únicamente train flags y conserva validation/test intactos. Así se prueba directamente si la supuesta limpieza mejora generalización.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D063 — Market Context necesita semántica temporal antes de ser feature

**Estado:** SUPPORTED como restricción de datos.

Hay 72 claves geo-sector y 30 meses globales, pero cada clave sólo tiene 3–12 meses, mediana 7, y ninguna cubre los 30 meses.

**Por qué importa.** Un `month` en una tabla no dice cuándo esa información estuvo realmente publicada o disponible. Forward-fill o nearest-month pueden introducir conocimiento que un scoring histórico no tenía.

**Decisión.** Esta batería no experimenta con Market Context. Preferimos perder una feature potencialmente útil a producir un lift no defendible.

**Qué permitiría retomarla.** Fecha efectiva/publicación, regla de cierre mensual y join as-of reproducible.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D064 — Availability tiene dos dimensiones: estado y frescura

**Estado:** SUPPORTED.

~90.27% de los spots cambia de availability al menos una vez. La separación entre snapshots tiene mediana de 21 días, p95 97, p99 155 y máximo 319.

**Por qué importa.** Elegir el último snapshot con `snapshot_date <= score_time` resuelve el leakage hacia el futuro, pero no resuelve **staleness**. Un snapshot de hace 150 días es legal pero puede ser poco representativo. Además, la edad del snapshot puede correlacionarse con periodo/cobertura y convertirse en proxy de drift.

**Qué no demuestra.** No demuestra que un snapshot viejo sea incorrecto ni que deba imputarse como unavailable.

**Qué lo resuelve.** E023 compara edad cruda, eliminación de edad y una representación protegida con log-age/buckets que trata >90d como contexto de disponibilidad desconocido.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D065 — El proxy actual limita la evidencia sobre matching

**Estado:** INCONCLUSIVE respecto al matching real.

Mismo estado/municipio/corredor y ratios simples de área/presupuesto apenas mueven scheduled_visit en crudo; un fit económico cercano a 1 no aparece consistentemente mejor.

**Por qué importa.** Si el generador de `scheduled_visit` no responde fuertemente a compatibilidad intuitiva, un experimento offline puede subestimar el valor real de matching. Esto es una limitación del **label/proxy**, no evidencia de que matching sea inútil.

**Qué no demuestra.** No invalida D023/D024 ni la suite de Matching A/B; precisamente refuerza la necesidad de una evaluación online/lead-level bien definida.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D066 — Los current-state aggregates de Spot no son snapshots históricos

**Estado:** SUPPORTED.

Con fin observable 2026-07-13, 373 spots (12.43%) tienen `days_on_market` mayor al tiempo transcurrido desde `created_at`; 17 implican más de un año hacia el futuro y el máximo es +694 días. `spots.total_inquiries` coincide exactamente con el conteo observable de inquiries sólo en 7.07% de spots.

**Por qué importa.** Utilizarlos retrospectivamente equivale a describir una fila histórica con un estado acumulado en otro momento. Eso sí puede convertirse en leakage/current-state contamination.

**Decisión.** `days_on_market`, `total_inquiries`, `total_views` e `is_active` permanecen BLOCK en el pipeline histórico.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D067 — prior_searches y prior_inquiries deben probarse por separado

**Estado:** SUPPORTED descriptivamente; valor incremental pendiente de E026.

Su correlación Pearson es -0.00495, prácticamente cero.

**Por qué importa.** Correlación cero no significa “una sobra”. Puede significar que capturan comportamientos distintos: exploración/búsqueda frente a contacto efectivo. Tampoco hay base para sumarlas en un único engagement score.

**Qué lo resuelve.** E026 realiza ablación de cada campo y de ambos conjuntamente bajo la misma baseline.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D068 — La dispersión de broker justifica una prueba, no una conclusión causal

**Estado:** INCONCLUSIVE.

Entre brokers con >=50 inquiries, scheduled_visit descriptivo va aproximadamente de 9.86% a 32.79%.

**Por qué importa.** La magnitud es suficiente para preguntar si existe señal histórica reutilizable. Pero la tasa full-dataset mezcla cartera, geografía, inventario, lead mix y periodo.

**Qué no demuestra.** No demuestra que reasignar un lead a un broker de tasa alta mejore conversión.

**Qué lo resuelve.** E027 construye un prior suavizado usando sólo respuestas realizadas estrictamente antes del score, sin usar `broker_id` como identidad de modelo. Aun si mejora predicción, routing causal seguirá requiriendo experimento online.

Evidencia: [EV-020](../Evidencias/EV-020_eda_profundo.md).

## D069 — T1 parecía fuerte, pero su señal está dominada por tiempo/progreso

**Estado:** SUPPORTED.

E022 responde una pregunta distinta a E005: no quién gana con el feature set disponible, sino cuánto del rendimiento depende de clocks sujetos a drift.

En el Random Forest especialista:

- macro AP: 0.5175 → **0.4850** al retirar temporal/progreso;
- macro AUC: 0.5561 → **0.5122**;
- ΔAP full−no-temporal: **+0.0325**, IC95% **[+0.0161, +0.0496]**;
- ΔAUC: **+0.0439**, IC95% **[+0.0257, +0.0625]**.

T1 concentra el problema:

- AUC 0.5877 → **0.5038**;
- AP 0.5628 → **0.5097**;
- ΔAUC **+0.0839**, IC95% **[+0.0494, +0.1208]**;
- ΔAP **+0.0531**, IC95% **[+0.0200, +0.0815]**.

Además, un diagnóstico `time_proxy_only` obtiene macro AUC **0.5960** y AP **0.5492**, por encima del RF completo.

**Interpretación:** D019 sigue siendo correcto como benchmark relativo dentro de E005, pero ya no puede sostener “T1 tiene una señal estable lista para producción”. El dataset sintético codifica fuertemente la cohorte/progreso del funnel.

**Decisión:** la versión T1 de E005 queda **BLOCK para producción**. Un release candidate debe retirar/reformular clocks, validarse en otra cohorte y demostrar que la señal restante no es sólo calendario.

Evidencia: [EV-022](../Evidencias/EV-022_temporal_feature_ablation.md).

## D070 — Freshness de Availability es guardrail, no ventaja predictiva demostrada

**Estado:** SUPPORTED.

Macro AP:

- raw snapshot age: 0.5175;
- sin raw age: **0.5236**;
- representación guarded: 0.5173.

La versión guarded vs raw tiene ΔAP -0.0002, IC95% [-0.0089, +0.0089], dentro del margen de no-inferioridad -0.01.

**Interpretación:** no hay argumento para premiar/castigar comercialmente a un lead por la edad cruda del snapshot. La edad sirve para saber **cuánto confiar en el estado de inventario**.

**Decisión:** eliminar raw age como predictor de negocio; conservar freshness explícita y tratar >90d como unknown histórico. En producción se prefiere inventory live.

Evidencia: [EV-023](../Evidencias/EV-023_availability_staleness.md).

## D071 — Eliminar outliers no está respaldado

**Estado:** NOT_SUPPORTED para una política automática de borrado.

Eliminar sólo anomalies de train:

- AP 0.5175 → 0.5237;
- ΔAP +0.0063, IC95% **[-0.0029, +0.0143]**;
- ΔAUC +0.0033, IC95% **[-0.0049, +0.0130]**.

**Interpretación:** el punto mejora, pero la incertidumbre permite tanto ausencia de beneficio como una mejora modesta. No hay base para declarar “los outliers son ruido”.

**Decisión:** conservar observaciones; usar anomaly detection como QA/diagnóstico, no como filtro automático del release candidate.

Evidencia: [EV-024](../Evidencias/EV-024_outlier_handling.md).

## D072 — Price totals: redundancia clara, decisión predictiva todavía estrictamente inconclusa

**Estado:** INCONCLUSIVE.

Al retirar los Spot totals casi deterministas:

- macro AP: 0.5175 → **0.5198**;
- macro AUC: 0.5561 → **0.5533**;
- ΔAP +0.0023, IC95% [-0.0078, +0.0104];
- ΔAUC -0.0028, IC95% **[-0.01017, +0.00468]**.

El margen pre-registrado era -0.01. El límite AUC queda apenas 0.00017 por debajo.

**Interpretación:** sería fácil cambiar el umbral después de ver el dato y declarar no-inferioridad; no se hace. Predictivamente no parecen esenciales, pero el contrato formal no pasó.

**Decisión:** mantener el resultado como inconcluso; por parsimonia son candidatos a retirar después de una confirmación temporal adicional.

Evidencia: [EV-025](../Evidencias/EV-025_redundancy_ablation.md).

## D073 — prior_searches no sólo es redundante: está deteriorando el modelo

**Estado:** SUPPORTED para este RF/split.

Macro AP:

- full: 0.5175;
- sin `prior_searches`: **0.5276**;
- sin `prior_inquiries`: 0.5236;
- sin ambas: 0.5239.

Para `prior_searches`, full−drop = **-0.0101 AP**, IC95% **[-0.0183, -0.0010]**. El signo negativo significa que quitarla mejora.

En T0, AP sube de 0.4683 a **0.4864** al retirarla.

Para `prior_inquiries`, el punto también favorece quitarla, pero su IC cruza cero.

**Decisión:** retirar `prior_searches` del release candidate. La utilidad de `prior_inquiries` queda no demostrada; por parsimonia no debe considerarse una feature “obligatoria”.

Evidencia: [EV-026](../Evidencias/EV-026_prior_history_ablation.md).

## D074 — La heterogeneidad bruta de broker no se convierte en un prior robusto

**Estado:** INCONCLUSIVE predictivamente; **NO-INCLUDE** operacionalmente.

Broker prior vs baseline:

- macro ΔAP **+0.0015**, IC95% **[-0.0086, +0.0120]**;
- macro ΔAUC **+0.0018**, IC95% **[-0.0080, +0.0116]**;
- T1 ΔAP +0.0101, IC95% [-0.0148, +0.0371];
- T2 ΔAP -0.0075, IC95% [-0.0227, +0.0091].

**Interpretación:** construir correctamente el historial point-in-time reduce mucho la aparente “calidad de broker” observada en tasas brutas. La composición de cartera/tiempo probablemente explica parte de la dispersión.

**Decisión:** no incorporar el prior en E028 ni cambiar routing de brokers por esta señal. Un efecto causal de broker requiere otro RCT.

Evidencia: [EV-027](../Evidencias/EV-027_broker_prior_point_in_time.md).

## D075 — E028 ya tiene protocolo definitivo; el release candidate existe, pero el launch gate sigue cerrado

**Estado:** SUPPORTED como decisión de lanzamiento.

El A/B definitivo está pre-registrado y el release candidate drift-sanitized ya fue construido y congelado en E029. Eso resuelve el blocker de **artifact inexistente**, pero no el blocker de **evidencia prospectiva**.

E029 retiró de LeadQuality:

- `score_weekday`, `score_hour`, `score_month`;
- `days_from_lead_creation`, `inquiry_number`, `days_since_first_inquiry`;
- `prior_searches`;
- Availability completa como señal predictiva;
- broker prior.

T0/T1 quedan neutrales y sólo T2 tiene artifact predictivo congelado.

El diagnóstico histórico del candidato es modesto pero no nulo:

- calibration partition AUC 0.543;
- AP/prevalencia 1.069;
- Lift@10 1.147x;
- PSI numérico máximo train→calibration 0.074.

Sin embargo, esos datos históricos ya participaron en la selección de política E021–E027. Por eso **no son confirmatorios** y no pueden abrir E028.

El gate válido requiere la primera cohorte genuinamente posterior al freeze:

1. mínimo 500 leads maduros first-T2;
2. AUC >=0.55;
3. lower IC95% AUC >0.50;
4. AP/prevalencia >=1.05;
5. Lift@10 >=1.10;
6. timestamp real de scheduled_visit >=99.5%;
7. ningún fallo de leakage/instrumentación.

**Decisión:** E028 está listo a nivel causal/estadístico y E029 está listo a nivel de artifact congelado, pero el lanzamiento permanece **BLOCKED_PENDING_PROSPECTIVE_GATE + production A/A**.

Evidencia: [EV-028](../Evidencias/EV-028_definitive_abt_target.md), [EV-029](../Evidencias/EV-029_drift_sanitized_release_candidate.md).

## D076 — Un scheduled_visit sin timestamp no es un negativo

**Estado:** SUPPORTED como restricción de target/datos.

En el paquete candidato `response_event_at` no viene como timestamp independiente; se reconstruye como `inquiry_at + broker_response_hours`. El EDA muestra que `broker_response_hours` falta en **14.97% de las filas scheduled_visit**.

**Problema.** Si existe un scheduled_visit pero no conocemos cuándo ocurrió, y su inquiry puede corresponder a la ventana `(score_time, score_time+30d]`, no podemos afirmar ni 1 ni 0. El pipeline histórico anterior descartaba esos eventos al exigir `response_event_at.notna()`; por tanto sus labels contienen cierta misclasificación hacia negativo.

**Nueva regla canónica.**

- evento conocido dentro de ventana → 1;
- observación completa sin evento → 0;
- scheduled_visit con timestamp desconocido que puede tocar la ventana → `AMBIGUOUS_UNKNOWN_EVENT_TIME`;
- right-censored → fuera de la evaluación binaria;
- visita ya observada antes del scoring → snapshot ineligible.

**Impacto sobre evidencia previa.** E021–E027 siguen siendo válidos para detectar drift, comparar feature policies y descubrir señales claramente inestables, especialmente porque el missingness de response hours es parecido entre categorías. Pero sus métricas absolutas no deben tratarse como calibración definitiva del target productivo.

**Producción.** E028 exige timestamp backend real de scheduled_visit con completitud >=99.5%. La falta de timestamp productivo es un blocker de instrumentación, nunca una razón para imputar outcome=0.

Implementación: [target_contract.py](../feature_validation/E028_definitive_opportunity_score_abt/target_contract.py). Evidencia: [EV-028](../Evidencias/EV-028_definitive_abt_target.md).

## D077 — La evaluación causal definitiva debe ser lead-level y sistémica

**Estado:** PROPOSAL pre-registrada.

La evaluación offline ha producido muchas preguntas útiles sobre arquitectura, perfiles, disponibilidad, drift y matching. Ninguna de ellas sustituye la pregunta final de producto: **¿usar el sistema cambia el resultado comercial de un lead?**

La propuesta E028 randomiza por `lead_id` antes de cualquier exposición experimental. El control conserva la priorización actual de Growth; el tratamiento activa el sistema dinámico completo T0/T1/T2, Inventory Serviceability y fallback.

La target primaria se fija como:

`lead_scheduled_visit_30d_from_assignment = 1`

si el lead tiene al menos un `scheduled_visit` durante los 30 días posteriores a `assignment_at`.

**Por qué no randomizar inquiries.** El tratamiento modifica la trayectoria del lead, puede cambiar cuántas inquiries ocurren y produce múltiples T2. Randomizar o analizar a nivel inquiry rompería independencia y permitiría que el propio tratamiento altere el denominador.

**Por qué scheduled_visit.** Es el evento observable más cercano a avance comercial real dentro de los datos disponibles. `accepted` es demasiado débil y cierre/venta no está disponible con maduración confiable en el paquete candidato. En producción, cierre/revenue a 90 días debe conservarse como north-star secundaria cuando exista ground truth.

**Por qué 30 días.** Fija una ventana operativa comparable entre cohortes y evita etiquetar como negativos a leads sólo porque fueron observados menos tiempo.

**Drift.** El power no se calcula suponiendo estable la tasa histórica de 34.3%. Se usa una planificación conservadora alrededor de p=0.50, MDE +2 pp, alpha 0.05 y power 80%: 9,806 leads maduros por brazo, 19,612 en total. El análisis reportará heterogeneidad por semana de asignación y no habrá optional stopping.

**Regla SHIP.** Delta ITT >= +2 pp, límite inferior del IC95% >0 y guardrails duros aprobados.

**Regla NO-SHIP.** Límite superior IC95% < +2 pp: el test descarta el mínimo efecto práctico pre-registrado.

El resto se considera INCONCLUSIVE; secondary metrics no pueden rescatar un primary fallido.

Evidencia: [EV-028](../Evidencias/EV-028_definitive_abt_target.md).

## D078 — El release candidate debe validarse después del freeze, no “confirmarse” con el histórico usado para elegirlo

**Estado:** SUPPORTED como regla de validación.

E029 ya congeló preprocessor, RF T2, calibrador, feature schema y hashes. Su historical calibration partition alcanza AUC 0.543, AP/prevalencia 1.069 y Lift@10 1.147x, mientras el rolling post-selection tiene AUC medio 0.534 y mínimos de AP/prevalencia/Lift inferiores a 1.

**Por qué importa.** E021–E027 usaron el histórico para decidir qué clocks, history fields y fuentes retirar. Volver a usar ese mismo periodo como “confirmación” produciría selection bias: estaríamos evaluando una política parcialmente diseñada con el conjunto que pretende validarla.

**Regla congelada.** El primer test confirmatorio debe comenzar con leads creados estrictamente después del freeze/data cutoff y cerrarse por semanas completas, extendiéndose sólo por N y nunca por outcomes. Si después de 16 semanas hay menos de 500 leads maduros, el resultado es `INCONCLUSIVE_INSUFFICIENT_SAMPLE`; los umbrales no se relajan post hoc.

**Implicación:** el repo ya contiene el evaluator `evaluate_prospective_gate.py`, por lo que este pendiente es de **datos futuros**, no de implementación.

Evidencia: [EV-029](../Evidencias/EV-029_drift_sanitized_release_candidate.md).



## D079 — La ABT definitiva separa modelado, política y auditoría

**Estado:** SUPPORTED.

E030 pasó todos los gates con 20,738 snapshots de auditoría, 18,237 model-ready y 4,648 leads. La separación de roles evita dos errores previos: convertir variables legales pero inestables en predictors y perder rows ambiguas/censuradas al forzar un label binario.

**Implicación:** E030 es la base contractual para toda nueva recuperación T0/T1/T2; no deben construirse datasets paralelos con targets o splits alternativos salvo experimento registrado.

Evidencia: [EV-030](../Evidencias/EV-030_definitive_abt.md).

## D080 — T0 no se recupera con la primera ola semántica

**Estado:** NOT_SUPPORTED como recovery.

La mejor representación elegida en validation fue soft_profiles, pero no calificó el gate de desarrollo. En test AUC=0.4897, AP/prevalence=0.964x y Lift@10=0.824x. Los deltas frente al atomic baseline cruzan ampliamente cero.

**Lectura:** no hay evidencia de que Need, specificity o un cluster outcome-free K=3 conviertan la información de alta disponible en un ranking útil. T0 neutral sigue siendo la política correcta hoy.

**Qué no implica:** que T0 sea imposible con nuevas fuentes o representaciones; sí implica que no debe forzarse un score usando estos campos actuales.

Evidencia: [EV-031](../Evidencias/EV-031_semantic_feature_engineering_ladder.md), [EV-032](../Evidencias/EV-032_t0_semantic_recovery.md).

## D081 — T1 semántico no rescata la señal perdida al retirar clocks

**Estado:** NOT_SUPPORTED.

Semantic interactions (Dynamic Need + PH/LOC + transitions) fue la mejor variante de validation, pero tampoco calificó. En test AUC cae de 0.4975 atomic a 0.4637 y el delta AUC tiene IC95% [-0.0664,-0.0022].

**Por qué importa:** el resultado anterior de Dynamic Need (EV-013) usaba otra formulación/proxy y un holdout ya consumido. Bajo la target E028 y el split E030, esa señal no se replica como LeadQuality T1.

**Decisión:** mantener Dynamic Need como representación de negocio/routing hypothesis, no como feature promovida de LeadQuality T1.

Evidencia: [EV-033](../Evidencias/EV-033_t1_semantic_recovery.md).

## D082 — Un cluster interpretable no es automáticamente una buena feature

**Estado:** SUPPORTED.

Dynamic Need tiene excelente separación geométrica (silhouette 0.620, ARI 1.000) y PH/LOC tienen semántica útil. Sin embargo, E031-E033 muestran que una segmentación estable puede no aportar generalización a la target canónica.

**Regla:** separar tres gates: calidad geométrica, interpretabilidad comercial y valor predictivo out-of-time. Pasar los dos primeros no autoriza el tercero.

Evidencia: [EV-013](../Evidencias/EV-013_matching_profiles_v4.md), [EV-033](../Evidencias/EV-033_t1_semantic_recovery.md).

## D083 — El test E030 ya fue consumido para recuperación T0/T1

**Estado:** SUPPORTED como gobernanza.

E032 y E033 reservaron el test para una evaluación one-shot después de seleccionar exclusivamente con validation. Desde este punto no debe utilizarse para declarar confirmación independiente de nuevas familias de FE.

**Implicación:** la segunda ola de FE puede desarrollarse con rolling CV/train-validation, pero cualquier promoción fuerte necesita nueva cohorte temporal o el gate prospectivo.

Evidencia: [EV-032](../Evidencias/EV-032_t0_semantic_recovery.md), [EV-033](../Evidencias/EV-033_t1_semantic_recovery.md), [EV-034](../Evidencias/EV-034_general_feature_engineering_catalog.md).


## D084 — La segunda ola de FE refuerza el no-signal de T0

**Estado:** NOT_SUPPORTED como recuperación.

E035 probó missingness, frequency encoding, quantile bins y transforms combinados en tres rolling folds dentro de E030 train. La mejor variante T0, missingness_frequency, obtiene mean AUC 0.4979, AP/prevalence 0.987x y min Lift@10 0.708x.

**Lectura:** la falta de señal T0 ya no puede atribuirse sólo a que faltaron clusters o transforms básicos. Con la información actual de intake no aparece una relación temporalmente estable con scheduled_visit_30d.

**Decisión:** no activar LeadQuality T0 con estos campos.

Evidencia: [EV-035](../Evidencias/EV-035_advanced_feature_engineering.md).

## D085 — La pista geo/inventory de T1 no es robusta

**Estado:** NOT_SUPPORTED.

E035 mostró una señal débil al combinar geo/inventory-relative. E036 separó los componentes en los mismos rolling folds:

- geo_distance mean AUC 0.4842;
- inventory_relative 0.4818;
- inventory_plus_geo 0.4887;
- inventory_geo_frequency 0.4820.

Ninguna variante consigue AUC >0.50 en un fold.

**Decisión:** no promover estos features a T1 LeadQuality. Pueden conservarse como ideas de matching si aparece una fuente de inventario temporalmente más rica.

Evidencia: [EV-036](../Evidencias/EV-036_t1_geo_inventory_decomposition.md).

## D086 — Target encoding temporal tampoco convierte T0/T1 en un buen propensity model

**Estado:** INCONCLUSIVE para valor futuro; no soportado para activación actual.

E037 usa encoding centrado, suavizado alpha=50 y fit sólo sobre el pasado de cada fold. En T0 permanece cerca de azar. En T1, te_interactions alcanza mean AUC 0.5052 y AP/prevalence 1.020x, con 2/3 folds por encima de 0.50, pero mean Lift@10=0.958x y el peor AUC=0.4966.

**Lectura:** puede existir heterogeneidad categórica histórica débil, pero no se traduce en concentración operacional útil.

**Decisión:** mantener target encoding como research-only/high-risk; no incorporarlo a ABT release.

Evidencia: [EV-037](../Evidencias/EV-037_temporal_smoothed_categorical_priors.md).

## D087 — T0/T1 no deben confundirse con “etapas apagadas”

**Estado:** SUPPORTED.

Los experimentos justifican que el **head de LeadQuality** sea neutral en T0/T1, pero no que el sistema ignore esas etapas.

- T0 conserva Search Need/specificity como representación explicativa y operativa.
- T1 conserva Dynamic Need, Need transition, PH/LOC y Lead×Spot fit para matching/routing experimental.
- T2 conserva el candidate predictivo E029.

Esta separación evita inventar propensión donde no existe sin desperdiciar semántica útil para decisiones distintas.

Evidencia: [EV-038](../Evidencias/EV-038_stage_aware_feature_policy.md).

## D088 — La siguiente mejora de T0/T1 debe venir de información nueva

**Estado:** SUPPORTED como decisión de investigación.

E031–E037 cubren clusters, transforms, interactions, missingness, frequency, bins, inventario relativo, geo-distance y target encoding temporal. Continuar buscando combinaciones sobre los mismos periodos aumenta la probabilidad de research overfitting.

**Regla de reapertura:** nueva fuente, target comercial mejor o nueva cohorte independiente.

Fuentes prioritarias:
- raw inquiry text;
- coordenadas canónicas de preferencia;
- market/inventory effective-dated;
- true close/lease outcome.

Evidencia: [EV-038](../Evidencias/EV-038_stage_aware_feature_policy.md).


## D089 — El texto bruto de inquiry no está disponible

**Estado:** SUPPORTED.

La inspección del esquema y búsquedas del repositorio confirman que `inquiries` contiene `message_length`, requested area/budget, urgency, channel y asked_visit, pero no `message_text`, `inquiry_text`, `message_body` ni equivalente.

**Por qué importa:** sin texto real, un experimento LLM de intención semántica no puede demostrar valor incremental. Generar texto sintético desde las columnas estructuradas sería circular.

**Decisión:** E039 queda `BLOCKED_BY_DATA_GAP`, no `FAILED`.

Evidencia: [EV-039](../Evidencias/EV-039_llm_semantic_inquiry_features.md).

## D090 — El LLM futuro debe ser extractor, no predictor libre

**Estado:** PROPOSAL.

Si Spot2 incorpora texto real de inquiries, el uso recomendado es convertir lenguaje no estructurado en variables auditables:

- intent/search maturity;
- urgency/timeline;
- constraints/flexibility;
- requested actions;
- specificity/ambiguity;
- Lead×Spot semantic compatibility;
- T2 intent trajectory.

El LLM no debe producir `conversion_probability`. La calibración de `target_scheduled_visit_30d` permanece en el modelo supervisado.

**Razón:** separa comprensión lingüística de estimación estadística y permite ablations por familia de features.

Evidencia: [EV-039](../Evidencias/EV-039_llm_semantic_inquiry_features.md).

## D091 — Feature Engineering T0/T1 está listo para cerrar con el dataset actual

**Estado:** SUPPORTED.

E031–E037 probaron familias semánticas, clusters, transforms, missingness, frequency, bins, geo/inventory y priors categóricos temporales. T0 no recuperó señal; T1 sólo mostró señales débiles/inestables. E030 test quedó consumido y E035–E037 evitaron reutilizarlo.

**Conclusión:** seguir iterando sobre las mismas columnas/periodos tendría una relación riesgo/valor desfavorable por research-overfitting.

**Criterio de reapertura:** nueva fuente, target comercial mejor, nueva temporalidad point-in-time o nueva cohorte independiente.

Evidencia: [EV-040](../Evidencias/EV-040_feature_engineering_closure.md).
