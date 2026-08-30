# Trazabilidad — caso de uso LLM

| Pregunta | Evidencia / análisis | Descubrimiento | Decisión |
|---|---|---|---|
| ¿T1 hace plausible interpretar intención? | [EV-001](../../Evidencias/EV-001_lead_attention.md), [EV-008](../../Evidencias/EV-008_llm_triage.md) | D001, D008 | Triage es plausible pero no demostrable sin raw text |
| ¿El LLM debe ser parte del predictor? | arquitectura de Lead Quality / matching existente | D019–D021, D049 | No forzarlo dentro del score |
| ¿LLM fallback tiene ventaja diferencial? | revisión del input disponible para matching/fallback | decisión de diseño, sin experimento | No seleccionado como caso principal |
| ¿Existe texto no estructurado útil en inventario? | `spots.title/description` + `spot_attributes` | [D050](../../conocimiento_agregado/DESCUBRIMIENTOS.md#d050--el-mejor-uso-llm-actual-es-auditar-la-calidad-semántica-del-inventario) | Probar auditoría semántica |
| ¿El LLM es mejor que reglas? | [EV-014](../../Evidencias/EV-014_llm_inventory_quality.md), [EV-015](../../Evidencias/EV-015_llm_inventory_semantic_audit.md) | D050 PROPOSAL, D051 SUPPORTED | Rules baseline ya ejecutado; comparación LLM sigue pendiente |
| ¿Qué tan difícil es el baseline? | [EV-015](../../Evidencias/EV-015_llm_inventory_semantic_audit.md) | D051 | Muy fuerte por copy templated: 12 oraciones, 322 spots candidatos |

## Assessment

La línea responde específicamente a:

- **Uso de IA (obligatorio):** uso explícito de un LLM con prompt, metodología y evaluación.
- **EDA / data quality:** añade consistencia semántica a nulls/outliers/rangos.
- **Inventory / fallback:** un listing con conflicto semántico puede convertirse, si el experimento lo valida, en un guardrail antes de recomendar alternativas.
- **Product vision:** una futura cola de Catalog QA puede evolucionar a un agente de corrección/revisión asistida.

La propuesta actual evita presentar como “IA de negocio” una tarea que un template resolvería de forma equivalente.


## Semantic v2 trace

`manual semantic discovery -> S001 Land×building-copy -> Rules v2 post-discovery -> disjoint holdout/challenge -> future human+LLM evaluation`

Evidence: [EV-015](../../Evidencias/EV-015_llm_inventory_semantic_audit.md). Discovery: D055.


## GPT-5 nano live result

Run `33296510774` completed successfully with 0 API/schema errors.

- holdout: 240/240 valid;
- challenge: 100/100 valid;
- cumulative observed live cost: USD 0.053522;
- S001 sensitivity: 76%;
- S001 specificity: 28%;
- conclusion: suitable for semantic discovery, not for automatic QA gating.

Evidence: [EV-016](../../Evidencias/EV-016_llm_gpt5nano_live.md).
