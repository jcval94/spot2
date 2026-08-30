# EV-008 — LLM triage

**Estado de evidencia:** conceptual; no existe comparación LLM-vs-no-LLM en los datos actuales. **No seleccionado como caso LLM principal del assessment** tras la reevaluación de arquitectura.

**Línea de trabajo:** [llm_triage](../llm_triage/)

## Evidencia fuente

- [Prompt de triage](../llm_triage/llm_triage_prompt.md)
- [EV-001](EV-001_lead_attention.md) respalda que existe valor predictivo al observar la primera interacción, no que el LLM cause ese valor.

## Uso defendible

Extracción de intención/restricciones, resumen, información faltante, SLA sugerido y razón transparente de prioridad.

## Caveat principal

No hay texto crudo de inquiry en el dataset candidato, por lo que no se puede estimar honestamente lift incremental del LLM.

## Decisión posterior

La idea se conserva como **Product Vision** para un futuro Broker Copilot, pero no como demostración principal del uso de IA en la entrega actual. Durante la reevaluación también se consideró un LLM para reranking/explicación de fallback; esa opción tampoco se seleccionó porque sus inputs son casi totalmente estructurados y Python + reglas + templates pueden resolver gran parte del trabajo con menor complejidad.

El caso actualmente preferido es [EV-014 — LLM Inventory Semantic Quality](EV-014_llm_inventory_quality.md), donde el LLM sí debe interpretar lenguaje libre y demostrar valor incremental contra un baseline de reglas.

La evolución completa se conserva en [registro_flujo/llm_use_case](../registro_flujo/llm_use_case/).

**Descubrimiento:** [D008](../conocimiento_agregado/DESCUBRIMIENTOS.md#d008--llm-utilidad-operacional-todavía-no-lift-demostrado).
