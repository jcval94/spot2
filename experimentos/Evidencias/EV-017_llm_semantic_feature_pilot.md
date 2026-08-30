# EV-017 — Low-cost LLM semantic feature pilot

## Estado

**NOT_SUPPORTED for promoting LLM-derived ABT features**

## Experimento

[`experimentos/llm_semantic_feature_pilot/`](../llm_semantic_feature_pilot/)

## Diseño

La prueba inicial está limitada a **100 spots**:

- 25 Rules-positive;
- 25 Land semantic residual;
- 25 ambiguity challenge;
- 25 clean controls.

El modelo default es `gpt-5-nano`, usado mediante Responses API + Structured Outputs.

## Justificación del LLM

El LLM no extrae variables que pueden obtenerse con reglas:

- claims literales;
- contradicciones directas;
- Land × building/interior copy ya conocido.

Su función experimental es únicamente descubrir **semántica residual**:

- cross-field coherence;
- sector/use-case mismatch;
- adaptive reuse plausibility;
- nuevos patrones repetibles no cubiertos por Rules.

## Variables LLM propuestas

- `llm_incremental_issue`;
- `llm_new_rule_candidate`;
- `llm_semantic_class`;
- `llm_actionability`;
- `llm_use_case_family`;
- `llm_adaptive_reuse_plausible`;
- `llm_requires_human_review`;
- `llm_confidence`;
- `llm_reason_code`.

No se produce rationale libre para reducir output tokens.

## Cost controls

- máximo default: 100 registros;
- batch size: 20;
- cinco requests para el piloto;
- reasoning minimal;
- verbosity low;
- compact payload;
- structured enum/boolean output;
- store=false;
- output token cap por batch;
- conteo real de tokens y costo persistido en CSV.

## Entregable esperado

`results/pilot_llm_results_100.csv`

Debe contener original text + structured fields + Rules + LLM outputs.

`results/pilot_usage_summary.csv`

contendrá tokens y costo.

## Resultados reales

### V1

- 100 registros;
- input tokens: 12,564;
- output tokens: 6,767;
- costo estimado: **USD 0.003335**.

V1 reveló una falla de contrato: `incremental_issue=false` para 100/100, pero algunos registros tenían simultáneamente `new_rule_candidate=true` o `requires_human_review=true`. Los outputs redundantes fueron rechazados.

### V2

Se repitieron los mismos 100 registros con un schema reducido y flags derivados en Python:

- input tokens: **12,634**;
- output tokens: **4,869**;
- costo estimado: **USD 0.002579**;
- clean-control incremental issue rate: **0%**;
- new rule candidates: **0/100**;
- residual actionable: **0/100**.

Por estrato:

- ambiguity challenge: 96% residual_ambiguous;
- clean control: 100% no_residual_issue;
- Land semantic residual: 8% residual_ambiguous;
- Rules-positive: 8% residual_ambiguous.

La aparente señal del ambiguity challenge ya estaba definida por reglas gratuitas. Los pocos residual ambiguities restantes también corresponden a combinaciones de flags determinísticos ya disponibles.

## Decisión

**NOT_SUPPORTED** para agregar variables LLM al ABT actual.

No se encontró cobertura semántica accionable/nueva que justifique costo o complejidad. En cumplimiento con la regla del usuario, las señales se convierten en variables determinísticas gratuitas mediante `build_rule_sidecar.py`.

Nuevas variables sin API:

- `rule_security_ambiguity_flag`;
- `rule_retail_adaptive_use_flag`;
- `rule_semantic_ambiguity_flag`;
- `rule_semantic_signal_count`;
- `rule_semantic_review_tier`.

Workflow V2: `33296462871`. Artifact: `9727563377`.

Reporte: [PILOT_REPORT.md](../llm_semantic_feature_pilot/results/PILOT_REPORT.md).


## Conocimiento acumulado

Relacionado con [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).


## Deterministic semantic sidecar — full catalog

The free rule sidecar was executed over all 3,000 spots:

- direct conflict flag: **322** (10.73%);
- Land × building-copy: **230** (7.67%);
- security ambiguity (claim + basic/cctv): **327** (10.90%);
- Retail adaptive-use language: **109** (3.63%);
- any semantic ambiguity flag: **429** (14.30%);
- listings with at least one semantic signal: **890**;
- listings with two simultaneous signals: **91**.

Review-tier distribution:

- none: 2,110;
- ambiguity: 386;
- direct_conflict: 322;
- cross_field: 182.

This sidecar is generated without OpenAI API calls.
