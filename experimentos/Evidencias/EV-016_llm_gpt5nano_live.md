# EV-016 — GPT-5 nano live semantic audit

**Estado:** empírica completa para ejecución live; gold labels humanos globales siguen pendientes.

## Fuente

- GitHub Actions run `33296510774` — success.
- Artifact `e015-live-gpt-5-nano`, id `9727712667`.
- Artifact SHA256: `a7c7d5ebdcd389c50d98917bb9d7adb263a56f9d39cb92da829280e1042f9be7`.
- [Live report](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/LIVE_GPT5_NANO_REPORT.md)
- [Prompt](../llm_inventory_quality/E015_llm_inventory_semantic_audit/prompts/system_prompt.md)
- [Schema](../llm_inventory_quality/E015_llm_inventory_semantic_audit/schema/audit_response.schema.json)
- [Holdout](../llm_inventory_quality/E015_llm_inventory_semantic_audit/labeling/labeling_holdout_v2.csv)
- [S001 challenge](../llm_inventory_quality/E015_llm_inventory_semantic_audit/labeling/semantic_challenge_v2.csv)

## Resultados

### Operación

- 240/240 holdout válidos;
- 100/100 challenge válidos;
- 0 errores;
- costo acumulado observado del live run: USD 0.053522;
- hard budget: USD 1.70.

### Holdout

- actionable: 194/240;
- overlap Rules v1: 110;
- incremental vs Rules v1: 84;
- overlap Rules v2: 117;
- incremental vs Rules v2: 77.

### S001 challenge

- sensitivity: 76%;
- specificity: 28%;
- precision vs discovery pattern: 51.35%.

## Conclusión

GPT-5 nano es técnicamente estable y extremadamente barato, pero sobre-alerta demasiado para utilizarse como gate automático de calidad. Se conserva como candidato para semantic discovery / rule discovery, no como decisión autónoma.

Los incrementales del holdout no son gold positives y no deben confundirse con lift de calidad real.

Descubrimiento: D056.
