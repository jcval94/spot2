# EV-018 — E015 live GPT-5 nano inventory audit

## Estado

**Empírica live completa.**

Experimento: [E015](../llm_inventory_quality/E015_llm_inventory_semantic_audit/)  
Reporte: [LIVE_GPT5_NANO_REPORT.md](../llm_inventory_quality/E015_llm_inventory_semantic_audit/results/LIVE_GPT5_NANO_REPORT.md)

## Corrida autoritativa

- workflow run: `33296510774`;
- status: SUCCESS;
- artifact: `9727712667`;
- artifact SHA256: `a7c7d5ebdcd389c50d98917bb9d7adb263a56f9d39cb92da829280e1042f9be7`;
- modelo: `gpt-5-nano`;
- hard budget: USD 1.70;
- costo acumulado observado: USD 0.053522.

## Holdout

- N=240;
- 0 errores;
- actionable 194;
- incremental vs Rules v1: 84;
- incremental vs Rules v2: 77.

Sin gold humano, esos incrementales son candidatos, no true positives.

## Challenge S001

- TP 38;
- TN 14;
- FP 36;
- FN 12;
- sensitivity 76%;
- specificity 28%;
- precision vs S001 discovery pattern 51.35%.

## Conclusión

GPT-5 nano es útil y extremadamente barato para semantic discovery, pero no alcanza specificity suficiente para gate automático.

Este resultado es consistente con EV-017: al controlar por reglas ya conocidas, no existe evidencia de una familia residual accionable que justifique convertir el LLM en feature del ABT.

Descubrimiento: D061.
