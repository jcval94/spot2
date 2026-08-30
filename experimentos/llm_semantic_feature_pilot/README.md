# E017 — Low-cost LLM semantic feature pilot

## Question

¿Existe señal semántica **incremental** en `spots.title + spots.description` que justifique pagar un LLM después de agotar reglas determinísticas?

## Decisión de diseño

No se usa un LLM para aquello que ya puede extraerse con costo prácticamente cero:

- claim de iluminación;
- claim de seguridad;
- claim de estacionamiento;
- claim de readiness/remodeling;
- contradicciones directas contra `natural_light`, `security_type`, `parking_spaces`, `building_status`;
- patrón Land × building/interior copy ya descubierto y promovible a regla;
- patrones lexicales explícitos.

El LLM se reserva para el **residuo semántico**:

- coherencia sector ↔ copy ↔ atributos;
- uso sugerido incompatible/ambiguo;
- adaptive reuse plausible;
- incoherencias cross-field no cubiertas por reglas;
- discovery de un nuevo patrón repetible.

## Modelo

Default: `gpt-5-nano`.

Motivo: Structured Outputs + Responses API y costo mínimo para clasificación/extracción.

Precios fijados en el script para estimación del piloto:

- input: USD 0.05 / 1M tokens;
- output: USD 0.40 / 1M tokens.

Antes de una corrida posterior conviene volver a confirmar pricing.

## Muestra de 100

`data/pilot_input_100.csv`

Muestra determinística de stress-test, no de prevalencia:

- 25 `rules_positive`;
- 25 `land_semantic_residual`;
- 25 `ambiguity_challenge`;
- 25 `clean_control`.

Esto permite evaluar:

1. si el LLM evita llamar incremental a algo ya cubierto por reglas;
2. si detecta semántica residual;
3. cuántos falsos positivos produce en controles;
4. si propone nuevos patrones accionables.

## Salida requerida

Cuando existe `OPENAIKEY`, se genera:

`results/pilot_llm_results_100.csv`

Cada fila conserva:

- `original_text`;
- campos estructurados relevantes;
- flags gratuitos de reglas;
- outputs LLM;
- modelo;
- batch;
- tokens;
- costo estimado.

Y:

`results/pilot_usage_summary.csv`

## Optimización de tokens

- batch de 20 registros → 5 llamadas para 100;
- un único prompt de sistema por batch;
- keys compactas en el payload;
- sólo campos necesarios para la decisión semántica;
- no se envían precios/geografía/IDs irrelevantes;
- Structured Outputs con enums/booleans en vez de explicación libre;
- `reasoning.effort=minimal`;
- `verbosity=low`;
- `store=false`;
- output libre de rationale largo.

En producción, las filas cubiertas por reglas **no deberían llamar al LLM**. Se incluyen aquí sólo como control experimental.

## Safety gate de costo

Por default, `run_pilot.py` rechaza más de 100 filas.

Sólo después de revisar este CSV se permite escalar explícitamente con `--allow-more-than-100`.

## Ejecución

```bash
export OPENAIKEY="..."
pip install -r experimentos/llm_semantic_feature_pilot/requirements.txt
python experimentos/llm_semantic_feature_pilot/run_pilot.py
```

## Resultado del piloto

### V1 — detectó un problema de contrato

100 registros reales procesados con `gpt-5-nano`:

- input tokens: 12,564;
- output tokens: 6,767;
- costo estimado: **USD 0.003335**.

La V1 produjo una contradicción de schema: 0/100 `incremental_issue=true`, pero simultáneamente 5 `new_rule_candidate=true` y 3 `requires_human_review=true`. Por eso esos campos no se aceptan para ABT.

### V2 — schema reducido y flags derivados en Python

La misma muestra de 100 se reejecutó con outputs independientes y menor output budget:

- input tokens: 12,634;
- output tokens: 4,869;
- costo estimado: **USD 0.002579**;
- reducción de output tokens vs V1: ~28%;
- clean-control incremental issue rate: **0%**;
- Rules-positive new-rule rate: **0%**;
- new rule candidates: **0/100**;
- residual actionable: **0/100**.

Por estrato:

- ambiguity challenge: 96% `residual_ambiguous`;
- clean controls: 100% `no_residual_issue`;
- Land semantic residual: 8% `residual_ambiguous`;
- Rules-positive: 8% `residual_ambiguous`.

La señal ambigua detectada por el LLM ya estaba cubierta por flags determinísticos (`rule_ambiguity_candidate_flag`, `rule_land_building_copy_flag` o sus interacciones).

## Decisión

**NOT_SUPPORTED para agregar variables LLM al ABT actual.**

El piloto no encontró señal semántica accionable/nueva que justifique costo o complejidad adicional. En cumplimiento con el criterio del experimento, la información se implementa como un sidecar gratuito de reglas:

`results/semantic_rule_sidecar_3000.csv`

Variables nuevas sin API:

- `rule_security_ambiguity_flag`;
- `rule_retail_adaptive_use_flag`;
- `rule_semantic_ambiguity_flag`;
- `rule_semantic_signal_count`;
- `rule_semantic_review_tier`.

Estas variables deben evaluarse predictivamente como challenger antes de entrar al ABT principal.

## Estado actual

**PILOT EXECUTED / LLM FEATURES NOT PROMOTED.**


## Documentación final

- [Decisión sobre features LLM](DECISION_LLM_FEATURES.md)
- [Reporte del piloto](results/PILOT_REPORT.md)
- [Historial de runs](results/RUN_HISTORY.md)
- [Estado](results/STATUS.md)
- [Evidencia canónica](../Evidencias/EV-017_llm_semantic_feature_pilot.md)

La corrida autoritativa es el workflow `33296462871` (SUCCESS), artifact `9727563377`.

Una reejecución posterior (`33296587433`) falló por `Batch 2 ID mismatch`; se documenta como un issue de robustez del runner y **no sustituye ni invalida** el resultado V2 exitoso.
