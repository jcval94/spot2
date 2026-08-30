# EV-015 — LLM Inventory Semantic Audit

**Estado de evidencia:** empírica parcial. Fase 0–1 ejecutadas y reproducidas en CI; comparación LLM pendiente.

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

## Trazabilidad de ejecución

- GitHub Actions: run `33289546496` — **success**.
- Governance CI: run `33289546474` — **success**.
- Artifact: `e015-offline-evidence`, id `9725519456`, digest `sha256:f98c46e99e6b71763b4b127723c24a45d900306697402b076a3b4151d9af9dd4`.
- Unit tests, full offline rebuild and evaluation-readiness check passed.

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


## Revisión semántica v2

La simulación manual del comportamiento esperado del LLM sobre la muestra de descubrimiento reveló una categoría que el baseline original no contemplaba: `semantic_cross_field_mismatch`.

Patrón principal:

- `sector_name=Land`;
- copy de edificio/interiores como “buena iluminación natural”, “recién remodelado”, “acabados modernos” o “listo para ocupar”.

Proyección sobre el catálogo completo:

- S001 aparece en 230 listings Land;
- 182 no estaban marcados por Rules v1;
- Rules v1: 322 spots únicos;
- Rules v2 post-discovery: 504 spots únicos;
- incremento: 182 spots, equivalente a 6.07% del inventario total.

Esta revisión también mostró que `unsupported_claim`, `not_verifiable` y `ambiguous` no deben contar como QA positives por defecto.

### Control de leakage de diseño

La muestra original de 200 listings fue utilizada para descubrir S001. Por lo tanto:

- se conserva `Rules v1` como baseline congelado;
- `Rules v2` se etiqueta explícitamente como post-discovery;
- la evaluación final se traslada a `labeling_holdout_v2.csv`, 240 filas sin solapamiento;
- se añade `semantic_challenge_v2.csv`, 100 filas Land (50 patrón / 50 control), también disjunto, exclusivamente para validar precision del patrón.

El challenge set no estima prevalencia.

### Evidencia v2

- [Semantic v2 report](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/SEMANTIC_V2_REPORT.md)
- [Semantic discovery summary](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/semantic_discovery_summary.json)
- [Semantic observations](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/semantic_discovery_observations.csv)
- [Clean holdout v2](../llm_inventory_quality/E015_llm_inventory_semantic_audit/labeling/labeling_holdout_v2.csv)
- [Semantic challenge v2](../llm_inventory_quality/E015_llm_inventory_semantic_audit/labeling/semantic_challenge_v2.csv)
- [Rules v2](../llm_inventory_quality/E015_llm_inventory_semantic_audit/src/rules_v2.py)

**Nuevo descubrimiento:** [D055](../conocimiento_agregado/DESCUBRIMIENTOS.md#d055--la-semantica-cross-field-descubre-un-patron-material-land--building-copy).


## Live continuation

La ejecución live del modelo económico quedó cerrada en [EV-018](EV-018_llm_inventory_nano_live.md).

Resultado: GPT-5 nano fue técnicamente estable y muy barato, pero su specificity de 28% en el challenge S001 impide recomendarlo como gate automático. La evaluación humana global sigue pendiente.
