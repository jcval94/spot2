# EV-008 — LLM triage

**Estado de evidencia:** conceptual; no existe comparación LLM-vs-no-LLM en los datos actuales.

**Línea de trabajo:** [llm_triage](../llm_triage/)

## Evidencia fuente

- [Prompt de triage](../llm_triage/llm_triage_prompt.md)
- [EV-001](EV-001_lead_attention.md) respalda que existe valor predictivo al observar la primera interacción, no que el LLM cause ese valor.

## Uso defendible

Extracción de intención/restricciones, resumen, información faltante, SLA sugerido y razón transparente de prioridad.

## Caveat principal

No hay texto crudo de inquiry en el dataset candidato, por lo que no se puede estimar honestamente lift incremental del LLM.

**Descubrimiento:** [D008](../conocimiento_agregado/DESCUBRIMIENTOS.md#d008--llm-utilidad-operacional-todavía-no-lift-demostrado).
