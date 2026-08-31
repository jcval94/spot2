# Referencias y trazabilidad — Entregable 1 EDA

> **Nota de trazabilidad:** los identificadores de evidencia se mantienen para auditoría, pero no es necesario abrir la evidencia histórica para entender la entrega final. La documentación presentada al evaluador es autocontenida y está en español.

Este archivo funciona como índice de evidencia. La jerarquía es deliberada:

1. **Codexway**: autoridad final.
2. **AssessmentSol1**: auditoría metodológica y evidencia complementaria.
3. **experimentos**: investigación histórica, challengers, resultados negativos e hipótesis.

Cuando dos fuentes usan poblaciones, targets o contratos temporales diferentes, el documento principal lo indica y no combina sus métricas.

## A. Autoridad final — Codexway

| ID | Evidencia | Uso en el EDA |
|---|---|---|
| C01 | **README de Codexway** | Contrato de producto, T1, arquitectura Lead Quality + Inventory y limitaciones |
| C02 | **Decisiones congeladas** | Reglas finales de temporalidad, clustering, Inventory y validación |
| C03 | **Leakage Matrix** | Allow/block de familias de variables |
| C04 | **Mapa fuente-evidencia** | Clasificación de evidencia heredada |
| C05 | **Resumen EDA** | Conteos, madurez y prevalencia T1 |
| C06 | **Lead mix** | Composición sector × modalidad |
| C07 | **Tasa por segmento** | Asociaciones descriptivas del proxy |
| C08 | **Market Context EDA** | Dinámica sectorial EDA_ONLY |
| C09 | **Frescura de inventario** | Sensibilidad 7/30/90 días |
| C10 | **Inventory audit** | UNKNOWN, bounds, confianza y limitación de listing state |
| C11 | **Cluster findings** | Resultado confirmatorio de perfiles/celdas |
| C12 | **Sensibilidad T0/T2** | Papel no principal de T0/T2 |
| C13 | **Sensibilidad de madurez** | Robustez de prevalencia T1 a 7/14/30 días |
| C14 | **Cronología** | Evolución de decisiones y correcciones |

## B. Auditoría complementaria — AssessmentSol1

| ID | Evidencia | Uso en el EDA |
|---|---|---|
| A01 | **Raw Data Audit** | Integridad relacional, missingness, outliers, joins temporales y Market Context |
| A02 | **EDA Findings** | Demand/supply, asked_visit, área, urgency, candidate depth y cautela estacional |
| A03 | **Drift Findings** | Separación population drift vs coverage/exposure/clock drift |
| A04 | **Feature Engineering Decisions** | Consecuencias de missingness y refinamiento T0→T1 |
| A05 | **Temporal Semantics** | Ontología de score times y observabilidad |
| A06 | **Demand vs supply** | Brecha sectorial DEVELOPMENT |
| A07 | **Resumen numérico** | Área, urgency, exposición, candidate depth y snapshot age |
| A08 | **Serie mensual T1** | Coverage drift y candidate depth temporal |
| A09 | **Inventory summary** | Missingness física y profundidad |
| A10 | **Market highlights** | Ejemplos por corredor/municipio |
| A11 | **T0 Exposure Drift** | Evidencia alternativa clean-room sobre exposure drift |
| A12 | **T2 Trajectory Decision** | Evidencia alternativa sobre valor marginal inestable de trayectoria |

> Nota de integración: AssessmentSol1 congela algunas decisiones distintas de Codexway —por ejemplo, otra definición de target T1 y una asunción explícita de inmutabilidad de atributos—. En este entregable esas decisiones **no sustituyen** el contrato final de Codexway.

## C. Investigación histórica — experimentos

| ID | Evidencia | Uso en el EDA |
|---|---|---|
| E01 | **EV-006 Profile Clustering v2** | Separación Persona/Need/Physical/Location y resultados negativos |
| E02 | **EV-013 Matching Profiles v4** | Dynamic Need, Broker Service y pockets locales |
| E03 | **Variable Treatment Manifest** | Missingness estructural por modalidad y tratamiento de variables |
| E04 | **Conocimiento agregado** | Síntesis de hallazgos experimentales |
| E05 | **EV-017 LLM Semantic Feature Pilot** | Valor del LLM como discovery semántico, no como feature final |
| E06 | **Semantic Rules Lift Ablation** | Resultado negativo: QA semántica no implica mejor ranking |
| E07 | **Matching A/B v3** | Auditorías de relaciones, Availability y matching |

## D. Requisito del assessment

- [Assessment oficial](../../assessment.md): define que el EDA debe ser una narrativa de negocio, cubrir calidad de datos, temporalidad, dinámica de mercado y explicar hipótesis que influyen en el sistema.

## E. Tablas finales de este entregable

- [Resumen de fuentes](tablas/00_resumen_fuentes.csv)
- [Métricas EDA clave](tablas/01_metricas_eda_clave.csv)
- [Hallazgos → decisiones](tablas/02_hallazgos_decisiones.csv)
- [Fuentes integradas](tablas/03_fuentes_integradas.csv)
