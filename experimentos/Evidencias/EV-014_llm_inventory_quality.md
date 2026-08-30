# EV-014 — LLM Inventory Semantic Quality

**Estado de evidencia:** diseño conceptual. La ejecución offline ya comenzó en [EV-015](EV-015_llm_inventory_semantic_audit.md); la comparación Rules-vs-LLM sigue pendiente.

**Línea de trabajo:** [llm_inventory_quality](../llm_inventory_quality/)

## Evidencia fuente

- [Problema y alcance](../llm_inventory_quality/README.md)
- [Plan experimental](../llm_inventory_quality/PLAN.md)
- [Arquitectura](../llm_inventory_quality/ARCHITECTURE.md)
- `data/candidate/csv/spots.csv`
- `data/candidate/csv/spot_attributes.csv`
- [Flujo de decisiones LLM](../registro_flujo/llm_use_case/)

## Observación que motiva el experimento

Un spot-check manual encontró ejemplos donde el copy comercial y los atributos estructurados parecen entrar en conflicto, como claims de iluminación natural con `natural_light=false` y claims de seguridad 24/7 con `security_type=none`.

Esto sólo demuestra que existen **casos candidatos**. No estima prevalencia, no establece automáticamente que el texto o el atributo sea la fuente correcta y no prueba que un LLM sea superior a reglas.

## Hipótesis

Rules + LLM puede detectar más inconsistencias semánticas relevantes que Rules-only, manteniendo precisión suficientemente alta para una cola de revisión de catálogo.

## Baseline obligatorio

El challenger del LLM no será “nada”. Será un motor de reglas explícitas de alta precisión sobre las mismas familias de claims.

## Gold standard

La comparación principal debe usar labels humanos estratificados. Otro LLM no puede ser el juez principal.

## Arquitectura seleccionada

- OpenAI Responses API directa;
- output estructurado;
- sin agente/ADK/LangChain en v1;
- Python conserva joins, reglas, métricas y decisiones determinísticas;
- el LLM sólo interpreta lenguaje y produce findings trazables.

## Uso de negocio

Detectar listings cuya redacción:

- contradice atributos;
- hace claims no soportados;
- requiere revisión antes de alimentar recomendaciones.

La primera integración es una **catalog QA queue**, no el Lead Opportunity Score.

## Caveats

- Texto sintético y altamente repetitivo: las reglas podrían ganar.
- Un conflicto texto-estructura no dice cuál fuente es correcta; sólo indica que debe revisarse.
- La semántica subjetiva no debe escalarse a `critical` sin un campo comparable.
- Todavía no existe evaluación de precision/recall.

## Criterio de éxito

El LLM debe demostrar cobertura incremental material frente a Rules-only con precisión alta sobre un holdout humano y con costo/latencia razonables.

## Continuación empírica

[E015 / EV-015](EV-015_llm_inventory_semantic_audit.md) ya ejecutó el perfilado del copy, el baseline Rules-only y preparó el gold set humano. La conclusión sobre el valor incremental del LLM permanece abierta.

**Descubrimientos relacionados:** [D050](../conocimiento_agregado/DESCUBRIMIENTOS.md#d050--el-mejor-uso-llm-actual-es-auditar-la-calidad-semántica-del-inventario), [D051](../conocimiento_agregado/DESCUBRIMIENTOS.md#d051--el-copy-sintético-hace-de-rules-only-un-baseline-fuerte).
