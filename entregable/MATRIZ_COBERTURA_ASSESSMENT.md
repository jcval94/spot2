# Matriz final de cobertura del assessment

> Estados permitidos: **COMPLETO**, **PARCIAL**, **FALTANTE**.
> Regla: una fila sólo se marca COMPLETO cuando existe un artefacto y evidencia trazable que cubren el requisito.

| Requisito del assessment | Artefacto | Sección | Evidencia | Estado |
|---|---|---|---|---|
| EDA — distribución por sector/modalidad/tipo de usuario | [EDA](01_eda/README.md) | Demanda y composición | 5,000 leads + tablas canónicas | COMPLETO |
| EDA — tasas de conversión/proxy por segmento | [EDA final](01_eda/EDA_FINAL.md) | Target, segmentos e hipótesis | Proxy T1 scheduled_visit; segmentación descriptiva | COMPLETO |
| EDA — temporalidad/estacionalidad | [EDA final](01_eda/EDA_FINAL.md) | T0/T1/T2, cohortes y drift | Cohortes temporales y coverage drift | COMPLETO |
| EDA — dinámica de mercado/corredor/municipio | [EDA final](01_eda/EDA_FINAL.md) | Mercado y geografía | Market Context usado sólo para EDA con caveat temporal | COMPLETO |
| EDA — missingness, outliers y sesgos | [EDA final](01_eda/EDA_FINAL.md) | Calidad de datos | Missingness, colas, structural missingness y drift | COMPLETO |
| EDA — hipótesis de conversión | [EDA final](01_eda/EDA_FINAL.md) | Hipótesis contrastadas | Hipótesis separadas en soportadas/inconclusas/rechazadas | COMPLETO |
| One-Pager — problema, enfoque, resultados, impacto | [One-Pager](02_one_pager/README.md) | Documento completo | Síntesis ejecutiva Codexway | COMPLETO |
| One-Pager — visualización ejecutiva | [HTML fuente](02_one_pager/ONE_PAGER_SPOT2_AESTHETIC.html) / [PDF](02_one_pager/ONE_PAGER_SPOT2.pdf) | Tres resultados, matriz operativa y plan de 90 días | Recomendación en español ejecutivo, legible en 60–90 segundos | COMPLETO |
| One-Pager — formato PDF de una página | [PDF](02_one_pager/ONE_PAGER_SPOT2.pdf) | Página Letter derivada del HTML | Fuente editorial única; PDF de una página con texto extraíble | COMPLETO |
| Lead Quality — feature engineering justificado | [Lead Quality](03_lead_quality/MODELO_CALIDAD_LEAD.md) | ABT y feature policy | Allowlist T1, PIT y ablations | COMPLETO |
| Lead Quality — selección/entrenamiento de modelos | [Lead Quality](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Selección final | stable_segment_logistic + Platt | COMPLETO |
| Lead Quality — AUC/PR/log-loss/Brier | [Lead Quality](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Evaluación | ROC-AUC 0.5478, PR-AUC 0.2391, Brier 0.1658, Log Loss 0.5129 | COMPLETO |
| Lead Quality — validación temporal | [Lead Quality](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Rolling temporal CV | Gate temporal + holdout procedimental | COMPLETO |
| Lead Quality — threshold/capacidad | [Lead Quality](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Política operativa | top 10% default; escenarios 5/10/20%; threshold validation ≈0.2531 | COMPLETO |
| Lead Quality — error analysis | [Lead Quality](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Error analysis / segmentos | Errores, segmentos y estabilidad mensual | COMPLETO |
| Lead Quality — calibración | [Lead Quality](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Calibration | Platt retenida por proper scoring | COMPLETO |
| Inventory — definición de disponibilidad/serviceability | [Inventory](04_inventory_fallback/README.md) | Estados y modelo conceptual | Disponible, no atendible, UNKNOWN/stale, lower/upper | COMPLETO |
| Inventory — restricciones reales | [Inventory](04_inventory_fallback/README.md) | Candidate Generation | Sector, modalidad, geografía, área, precio y PIT | COMPLETO |
| Inventory — point-in-time availability | [Inventory](04_inventory_fallback/README.md) | Backward as-of | 0 future snapshot violations | COMPLETO |
| Inventory — inventario insuficiente | [Inventory](04_inventory_fallback/README.md) | Fallback / NO_RESULT | UNKNOWN ≠ UNAVAILABLE; abstención gobernada | COMPLETO |
| Opportunity — fórmula de combinación | [Opportunity](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md) | Arquitectura final | p_quality × inventory_serviceability_lower + upper bound | COMPLETO |
| Opportunity — distribución y bandas | [Opportunity](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md) | Thresholds/capacidad y monitoring | lower/upper, bands y distribución | COMPLETO |
| Opportunity — estrategia fallback | [Inventory/Fallback](04_inventory_fallback/README.md) + [Opportunity](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md) | Fallback | top-3 interno; hasta 5 visibles; reason codes; NO_RESULT | COMPLETO |
| Opportunity — evaluación combinada alineada al éxito de fallback | [Opportunity](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md) | Trade-off y evaluación | Absolute Lift@10 1.370x; target T1 no observa éxito de fallback; incremental Inventory NO-GO | PARCIAL |
| Producción — pipeline entrenamiento/predicción | [Arquitectura](05_opportunity_produccion/02_ARQUITECTURA_PRODUCCION.md) | Flujo online T1 / registry | Arquitectura híbrida y contratos por componente | COMPLETO |
| Producción — monitoreo | [Runbook](05_opportunity_produccion/03_MONITOREO_GOBIERNO_RUNBOOK.md) | Panel mínimo | Base rate, Lift@K, calibration, drift, Inventory, latency | COMPLETO |
| Producción — drift | [Runbook](05_opportunity_produccion/03_MONITOREO_GOBIERNO_RUNBOOK.md) | Taxonomía de drift | Population/label/process/inventory/instrumentation/model | COMPLETO |
| Producción — retraining/rollback | [Runbook](05_opportunity_produccion/03_MONITOREO_GOBIERNO_RUNBOOK.md) | Retraining + rollback | Gates, champion/challenger y last-known-good | COMPLETO |
| Producción — latencia/volumen | [Arquitectura](05_opportunity_produccion/02_ARQUITECTURA_PRODUCCION.md) | SLO/SLA y escalabilidad | Targets explícitos identificados como propuestos, no medidos | COMPLETO |
| IA — uso real de LLM | [Uso de IA](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md) | E017 / E015 live | GPT-5 nano real, Structured Outputs y costos reales | COMPLETO |
| IA — prompt utilizado | [Uso de IA](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md) | Prompt exacto E017 V2 | Prompt preservado literalmente | COMPLETO |
| IA — qué funcionó y qué no | [Uso de IA](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md) | Resultado y governance | Discovery sí; ABT features no; automatic gate no; rules scoring no | COMPLETO |
| IA — reproducibilidad/costo/privacidad/fallback | [Uso de IA](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md) | Governance | Cache/schema/budget/store=false/opt-in/no score dependency | COMPLETO |
| Product Vision — máximo 2 párrafos | [Product Vision ejecutiva](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md) | Documento completo | Entry point oficial en dos párrafos | COMPLETO |
| Product Vision — tres meses adicionales | [Product Vision ejecutiva](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md) | Párrafo 1 | Instrumentación → challengers → shadow/RCT | COMPLETO |
| Product Vision — integración al producto | [Product Vision ejecutiva](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md) | Párrafo 1 | CRM/queue con Quality, Inventory, Opportunity y acción | COMPLETO |
| Product Vision — datos adicionales | [Product Vision ejecutiva](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md) | Párrafo 2 | Versionado, exposures, visitas, cierres, SLA, human gold | COMPLETO |
| Product Vision — causalidad | [Diseño causal](07_ia_product_vision/03_EXPERIMENTACION_CAUSAL.md) | RCT / alternativas | 50/50 sticky, ITT, SRM, interference, ramp-up, DiD | COMPLETO |
| Formato — notebook reproducible | [Notebook HTML](../codexway/notebooks/spot2_assessment.html) / [IPYNB](../codexway/notebooks/spot2_assessment.ipynb) | 9 capítulos; 82 celdas totales; 35 celdas de código ejecutadas; lecturas, auditoría, EDA, caso lead 6 y código plegable | IPYNB conserva ejecución top-to-bottom sin errores en sus 35 celdas de código; HTML autónomo sincronizado con la Parte 1 ampliada | COMPLETO |
| Formato — prompt de IA dentro del notebook | [Notebook IPYNB](../codexway/notebooks/spot2_assessment.ipynb) | Sección LLM | El notebook contiene el prompt del Semantic Inventory Quality Auditor | COMPLETO |
| Formato — slides PDF 5–8 slides | [Deck ejecutivo final](06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.pdf) / [HTML fuente](06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.html) | 7 slides, narrativa ejecutiva y caso reproducible | PDF de 7 páginas validado contra las decisiones canónicas de Codexway | COMPLETO |
| Formato — paquete mínimo de envío | [ZIP final](SPOT2_ASSESSMENT_FINAL.zip) / [Léeme primero](00_LEEME_PRIMERO.md) | Deck, One Pager y notebook en dos formatos | Cinco archivos exactos, no vacíos y legibles | COMPLETO |

## Lectura del estado

No hay requisitos marcados **FALTANTE** en el contenido técnico y ejecutivo construido.

El único punto **PARCIAL** es deliberado:

1. **Evaluación conjunta de Opportunity/Fallback:** existe evaluación offline, pero el target T1 no observa directamente éxito de fallback y el valor incremental de Inventory no está demostrado.

El deck, el One Pager, el notebook y el ZIP mínimo ya fueron reconstruidos, validados y conectados desde la portada final.
