# Referencias y trazabilidad — Entregable 1 EDA

Este archivo funciona como índice de evidencia. La jerarquía es deliberada:

1. **Codexway**: autoridad final.
2. **AssessmentSol1**: auditoría metodológica y evidencia complementaria.
3. **experimentos**: investigación histórica, challengers, resultados negativos e hipótesis.

Cuando dos fuentes usan poblaciones, targets o contratos temporales diferentes, el documento principal lo indica y no combina sus métricas.

## A. Autoridad final — Codexway

| ID | Evidencia | Uso en el EDA |
|---|---|---|
| C01 | [README de Codexway](../../codexway/README.md) | Contrato de producto, T1, arquitectura Lead Quality + Inventory y limitaciones |
| C02 | [Decisiones congeladas](../../codexway/evidence/DECISIONS.md) | Reglas finales de temporalidad, clustering, Inventory y validación |
| C03 | [Leakage Matrix](../../codexway/evidence/LEAKAGE_MATRIX.md) | Allow/block de familias de variables |
| C04 | [Mapa fuente-evidencia](../../codexway/evidence/SOURCE_EVIDENCE_MAP.md) | Clasificación de evidencia heredada |
| C05 | [Resumen EDA](../../codexway/outputs/metrics/eda_summary.json) | Conteos, madurez y prevalencia T1 |
| C06 | [Lead mix](../../codexway/outputs/tables/lead_mix.csv) | Composición sector × modalidad |
| C07 | [Tasa por segmento](../../codexway/outputs/tables/target_rate_by_segment.csv) | Asociaciones descriptivas del proxy |
| C08 | [Market Context EDA](../../codexway/outputs/tables/market_context_eda.csv) | Dinámica sectorial EDA_ONLY |
| C09 | [Frescura de inventario](../../codexway/outputs/tables/inventory_freshness_sensitivity.csv) | Sensibilidad 7/30/90 días |
| C10 | [Inventory audit](../../codexway/outputs/metrics/inventory_audit.json) | UNKNOWN, bounds, confianza y limitación de listing state |
| C11 | [Cluster findings](../../codexway/outputs/CLUSTER_FINDINGS.md) | Resultado confirmatorio de perfiles/celdas |
| C12 | [Sensibilidad T0/T2](../../codexway/outputs/metrics/t0_t2_sensitivity_metrics.json) | Papel no principal de T0/T2 |
| C13 | [Sensibilidad de madurez](../../codexway/outputs/tables/target_maturity_sensitivity.csv) | Robustez de prevalencia T1 a 7/14/30 días |
| C14 | [Cronología](../../codexway/evidence/CHRONOLOGY.md) | Evolución de decisiones y correcciones |

## B. Auditoría complementaria — AssessmentSol1

| ID | Evidencia | Uso en el EDA |
|---|---|---|
| A01 | [Raw Data Audit](../../AssessmentSol1/evidence/DATA_AUDIT.md) | Integridad relacional, missingness, outliers, joins temporales y Market Context |
| A02 | [EDA Findings](../../AssessmentSol1/evidence/EDA_FINDINGS.md) | Demand/supply, asked_visit, área, urgency, candidate depth y cautela estacional |
| A03 | [Drift Findings](../../AssessmentSol1/evidence/DRIFT_FINDINGS.md) | Separación population drift vs coverage/exposure/clock drift |
| A04 | [Feature Engineering Decisions](../../AssessmentSol1/evidence/FEATURE_ENGINEERING_DECISIONS.md) | Consecuencias de missingness y refinamiento T0→T1 |
| A05 | [Temporal Semantics](../../AssessmentSol1/evidence/TEMPORAL_SEMANTICS.md) | Ontología de score times y observabilidad |
| A06 | [Demand vs supply](../../AssessmentSol1/outputs/eda/demand_inventory_sector_gap.csv) | Brecha sectorial DEVELOPMENT |
| A07 | [Resumen numérico](../../AssessmentSol1/outputs/eda/numeric_summary.csv) | Área, urgency, exposición, candidate depth y snapshot age |
| A08 | [Serie mensual T1](../../AssessmentSol1/outputs/eda/monthly_t1_development.csv) | Coverage drift y candidate depth temporal |
| A09 | [Inventory summary](../../AssessmentSol1/outputs/eda/inventory_summary.csv) | Missingness física y profundidad |
| A10 | [Market highlights](../../AssessmentSol1/outputs/eda/market_context_highlights.csv) | Ejemplos por corredor/municipio |
| A11 | [T0 Exposure Drift](../../AssessmentSol1/evidence/T0_EXPOSURE_DRIFT.md) | Evidencia alternativa clean-room sobre exposure drift |
| A12 | [T2 Trajectory Decision](../../AssessmentSol1/evidence/T2_TRAJECTORY_DECISION.md) | Evidencia alternativa sobre valor marginal inestable de trayectoria |

> Nota de integración: AssessmentSol1 congela algunas decisiones distintas de Codexway —por ejemplo, otra definición de target T1 y una asunción explícita de inmutabilidad de atributos—. En este entregable esas decisiones **no sustituyen** el contrato final de Codexway.

## C. Investigación histórica — experimentos

| ID | Evidencia | Uso en el EDA |
|---|---|---|
| E01 | [EV-006 Profile Clustering v2](../../experimentos/Evidencias/EV-006_profile_clustering_v2.md) | Separación Persona/Need/Physical/Location y resultados negativos |
| E02 | [EV-013 Matching Profiles v4](../../experimentos/Evidencias/EV-013_matching_profiles_v4.md) | Dynamic Need, Broker Service y pockets locales |
| E03 | [Variable Treatment Manifest](../../experimentos/abt_feature_engineering/variable_treatment_manifest.csv) | Missingness estructural por modalidad y tratamiento de variables |
| E04 | [Conocimiento agregado](../../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md) | Síntesis de hallazgos experimentales |
| E05 | [EV-017 LLM Semantic Feature Pilot](../../experimentos/Evidencias/EV-017_llm_semantic_feature_pilot.md) | Valor del LLM como discovery semántico, no como feature final |
| E06 | [Semantic Rules Lift Ablation](../../experimentos/semantic_rules_lift_ablation/results/REPORT.md) | Resultado negativo: QA semántica no implica mejor ranking |
| E07 | [Matching A/B v3](../../experimentos/Evidencias/EV-010_matching_ab_v3.md) | Auditorías de relaciones, Availability y matching |

## D. Requisito del assessment

- [Assessment oficial](../../assessment.md): define que el EDA debe ser una narrativa de negocio, cubrir calidad de datos, temporalidad, dinámica de mercado y explicar hipótesis que influyen en el sistema.

## E. Tablas finales de este entregable

- [Resumen de fuentes](tablas/00_resumen_fuentes.csv)
- [Métricas EDA clave](tablas/01_metricas_eda_clave.csv)
- [Hallazgos → decisiones](tablas/02_hallazgos_decisiones.csv)
- [Fuentes integradas](tablas/03_fuentes_integradas.csv)
