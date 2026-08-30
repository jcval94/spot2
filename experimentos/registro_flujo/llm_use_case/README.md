# Flujo — Selección del caso de uso LLM

**Estado:** ACTIVE — caso de uso seleccionado; experimento pendiente.

## Pregunta original

¿Cómo cumplir el uso obligatorio de IA del assessment de Spot2 de forma que el LLM resuelva un problema de negocio real y no sea una capa decorativa alrededor de los modelos?

## Respuesta actual

El uso principal recomendado es un **LLM Semantic Inventory Quality Auditor**.

Su trabajo será interpretar claims de `spots.title/description` y contrastarlos con `spot_attributes` y campos estructurados. El baseline será Rules-only y la evaluación principal utilizará labels humanos.

## Qué se descartó como uso principal

Se consideraron:

1. triage de inquiry / Broker Copilot;
2. LLM-assisted fallback reranking y explicación;
3. generación de mensajes/templates a partir del score.

No se declaran “refutados experimentalmente”. Se consideran **no seleccionados por diseño para esta entrega**:

- no existe raw inquiry text para probar de manera honesta el triage semántico;
- el fallback actual parte casi totalmente de datos estructurados que Python puede filtrar/rankear;
- la explicación de esos campos puede resolverse con templates;
- por tanto, el LLM tenía una ventaja diferencial débil.

La nueva propuesta sí explota un tipo de información que requiere interpretación lingüística: el copy libre de los listings.

## Navegación

- [Cronología](CRONOLOGIA.md)
- [Decisiones](DECISIONES.md)
- [Trazabilidad](TRAZABILIDAD.md)
- [Incidencias y correcciones](INCIDENCIAS_Y_CORRECCIONES.md)
- [EV-008 — propuesta histórica de triage](../../Evidencias/EV-008_llm_triage.md)
- [EV-014 — propuesta actual de Inventory Semantic Quality](../../Evidencias/EV-014_llm_inventory_quality.md)
- [Plan actual](../../llm_inventory_quality/PLAN.md)
