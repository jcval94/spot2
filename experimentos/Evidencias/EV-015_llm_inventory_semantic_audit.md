# EV-015 — LLM Inventory Semantic Audit

**Estado de evidencia:** empírica parcial. Fase 0–1 ejecutadas sobre el catálogo completo; comparación LLM pendiente.

**Experimento:** [E015_llm_inventory_semantic_audit](../llm_inventory_quality/E015_llm_inventory_semantic_audit/)

## Evidencia fuente

- [Offline report](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/OFFLINE_REPORT.md)
- [Copy profile](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/copy_profile_summary.json)
- [Sentence counts](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/description_sentence_counts.csv)
- [Rules summary](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/rules_summary.json)
- [All candidate rule issues](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/rule_candidate_issues.csv)
- [Sector distribution](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/rule_flags_by_sector.csv)
- [Human labeling sample](../llm_inventory_quality/E015_llm_inventory_semantic_audit/labeling/labeling_sample.csv)
- [Labeling guide](../llm_inventory_quality/E015_llm_inventory_semantic_audit/labeling/LABELING_GUIDELINES.md)
- [Prompt](../llm_inventory_quality/E015_llm_inventory_semantic_audit/prompts/system_prompt.md)
- [Structured-output schema](../llm_inventory_quality/E015_llm_inventory_semantic_audit/schema/audit_response.schema.json)
- [Rules code](../llm_inventory_quality/E015_llm_inventory_semantic_audit/src/rules.py)
- [OpenAI client](../llm_inventory_quality/E015_llm_inventory_semantic_audit/src/openai_auditor.py)

## Hallazgos offline

Sobre 3,000 spots:

- 856 descripciones exactas únicas;
- 84.37% de filas comparten su descripción exacta con al menos otro spot;
- sólo 12 oraciones distintas componen todas las descripciones;
- Rules-only identifica 330 conflictos candidatos en 322 spots únicos (10.73%);
- natural_light: 153;
- readiness: 101;
- security: 55;
- parking: 21.

Tasa de spots con al menos un flag:

- Land: 13.48%;
- Industrial: 12.36%;
- Retail: 9.15%;
- Office: 8.88%.

## Qué demuestra

- el copy es altamente sintético/templated;
- existen suficientes conflictos estructurados-vs-texto candidatos para justificar auditar la consistencia;
- Rules-only es un challenger fuerte, no un baseline trivial.

## Qué NO demuestra

- que los 322 listings sean errores reales;
- que el texto sea correcto y el atributo incorrecto;
- que el LLM encuentre más issues;
- que el LLM deba desplegarse.

## Gold standard

Se prepararon 200 listings: 25 Rules-positive y 25 Rules-negative por sector. Los labels humanos se mantienen vacíos hasta revisión real.

## Próximo gate

Ejecutar LLM-only con `OPENAIAPI`, congelar labels humanos sin ver output del modelo y comparar:

Rules-only vs LLM-only vs Rules+LLM.

**Descubrimiento relacionado:** [D051](../conocimiento_agregado/DESCUBRIMIENTOS.md#d051--el-copy-sintético-hace-de-rules-only-un-baseline-fuerte).
