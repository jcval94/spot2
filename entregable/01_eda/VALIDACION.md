# Validación del Entregable 1 — EDA

**Estado:** PASS

Esta validación revisa la integridad del paquete final sin cambiar ninguna decisión de Codexway.

## 1. Completitud del paquete

- README de entrada: PASS
- Documento principal: PASS
- Referencias: PASS
- Figuras: **6**
- Tablas resumen: **4**
- Enlaces relativos rotos: **0**

## 2. Reconciliación de cifras críticas

| Claim del EDA | Fuente verificada | Resultado |
|---|---|---|
| T1 maduros = 4,898 | codexway/outputs/metrics/eda_summary.json | PASS |
| T1 positivos = 1,001 | 4,898 × 0.204369... | PASS |
| T1 prevalence = 20.44% | codexway/outputs/metrics/eda_summary.json | PASS |
| Inventory exact unknown = 44.30% | codexway/outputs/metrics/inventory_audit.json | PASS |
| Retail demand-supply gap = +5.89 pp | AssessmentSol1/outputs/eda/demand_inventory_sector_gap.csv | PASS; COMPLEMENTARIA |
| Nearest Availability usaría futuro en 7,758 inquiries / 34.36% | AssessmentSol1/evidence/DATA_AUDIT.md | PASS; AUDITORÍA |
| Codexway confirmatory clusters: 0/19 celdas BH-FDR 10% | codexway/outputs/CLUSTER_FINDINGS.md | PASS |
| Fresh candidates <=7d = 19.16%; leads con alguno = 93.46% | codexway/outputs/tables/inventory_freshness_sensitivity.csv | PASS |

## 3. Control de autoridad

### Codexway

Se mantiene como autoridad para:

- scoring moment T1;
- target principal;
- política de features;
- Availability backward as-of;
- UNKNOWN como incertidumbre;
- límites de listing state;
- Market Context EDA_ONLY;
- decisión confirmatoria de clustering.

**Resultado: PASS.**

### AssessmentSol1

Se usa únicamente como:

- auditoría relacional;
- cuantificación DEVELOPMENT;
- drift/coverage;
- missingness;
- candidate depth;
- demand/supply;
- stress metodológico.

No se promueve su target alternativo ni su asunción de inmutabilidad de atributos sobre la decisión final de Codexway.

**Resultado: PASS.**

### experimentos

Se usa únicamente como:

- evidencia histórica;
- challengers;
- Dynamic Need;
- pockets locales;
- semantic QA;
- resultados negativos;
- tratamiento exploratorio de variables.

El pocket DN4×LOC1×BSV1 se identifica explícitamente como histórico y no se convierte en multiplicador.

**Resultado: PASS.**

## 4. Contradicciones resueltas explícitamente

| Tema | Evidencia alternativa | Resolución final |
|---|---|---|
| Target T1 | AssessmentSol1 usa un proxy T1 diferente | Prevalecen definición y cifras Codexway |
| Spot attributes históricos | AssessmentSol1 explora una asunción de inmutabilidad | Codexway mantiene el claim histórico completo como CONDITIONAL |
| Dynamic Need | Experimentos muestran señal y transición útil | Codexway rechaza dynamic_need_profile en gate actual; queda el concepto, no el ID |
| Pockets locales | Experimentos encuentran lifts locales | Codexway 0/19 BH-FDR; quedan como hipótesis |
| Semantic flags | Experimentos encuentran QA material | Ablation no soporta uso en Lead Quality; queda Inventory QA |

## 5. Reglas de interpretación verificadas

- No se presenta market_context como historical model feature.
- No se presenta total_inquiries como feature T1.
- No se presenta UNKNOWN como UNAVAILABLE.
- No se presenta nearest Availability como método válido.
- No se presenta una asociación univariada como causalidad.
- No se presenta share de catálogo como serviceability.
- No se presenta un resultado de clustering histórico como modelo final.
- No se presentan métricas de AssessmentSol1 como si pertenecieran al modelo final de Codexway.

## 6. Alcance

La validación corresponde **únicamente al Entregable 1 — EDA**. No modifica ni evalúa otros entregables.
