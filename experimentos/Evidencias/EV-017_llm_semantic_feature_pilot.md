# EV-017 — Low-cost LLM semantic feature pilot

## Estado

**READY_FOR_API_PILOT / NOT YET EXECUTED**

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

## Estado de ejecución

En la sesión de implementación no estaba disponible `OPENAIKEY` ni `OPENAI_API_KEY`. Se abrió el flujo seguro de configuración de una OpenAI API key.

Por disciplina experimental **no se simula ni fabrica el CSV LLM**.

La evidencia se actualizará sólo después de una corrida real.


## Conocimiento acumulado

Relacionado con [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
