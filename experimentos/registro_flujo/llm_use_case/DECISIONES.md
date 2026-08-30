# Decisiones — caso de uso LLM

## D-LLM-01 — No forzar el LLM dentro del predictor

**Decisión:** Lead Quality e Inventory Availability siguen siendo responsabilidad de modelos/tabular logic apropiados.

**Estado:** vigente.

**Razón:** el uso obligatorio de IA no implica que el LLM deba mejorar AUC ni formar parte del score.

## D-LLM-02 — Triage no es la demostración principal

**Decisión:** mantener el triage semántico como visión futura.

**Estado:** vigente; refinado por el caso actual.

**Razón:** falta raw inquiry text; no existe una comparación LLM-vs-no-LLM honesta con el dataset candidato.

## D-LLM-03 — Descartar fallback reranking como uso principal

**Decisión:** no implementar primero un LLM que sólo rerankee candidatos ya descritos completamente por variables estructuradas o que genere explicaciones de esos campos.

**Estado:** descartado por diseño, **no refutado experimentalmente**.

**Razón:** reglas + función de distancia + templates pueden resolver gran parte del problema con menor costo, variabilidad y complejidad. No existía una necesidad lingüística suficientemente fuerte.

## D-LLM-04 — Seleccionar Semantic Inventory Quality

**Decisión:** el siguiente uso a probar es la detección de inconsistencias entre copy del listing y atributos estructurados.

**Estado:** actual.

**Razón:** aquí sí existe información no estructurada y una tarea semántica que no se reduce trivialmente a templates.

## D-LLM-05 — Baseline antes del LLM

**Decisión:** construir Rules-only antes de ejecutar OpenAI.

**Estado:** actual.

**Razón:** el LLM debe demostrar valor incremental contra una alternativa sencilla, no contra ausencia de solución.

## D-LLM-06 — Gold standard humano

**Decisión:** otro LLM no será el juez primario.

**Estado:** actual.

**Razón:** evita circularidad y permite estimar falsos positivos reales.

## D-LLM-07 — API directa, no agente en v1

**Decisión:** OpenAI Responses API directa + output estructurado.

**Estado:** actual.

**Razón:** el flujo es corto y stateless. No requiere tools, handoffs, sesiones ni loops. Agents SDK/ADK/LangChain sólo se reconsideran si el sistema evoluciona a un workflow autónomo de QA.


## D-LLM-08 — Separate actionability from observability

**Decision:** unsupported/not-verifiable/ambiguous claims are informational and do not count as positive QA predictions.

**Status:** current.

**Reason:** absence of a comparable field is not evidence that marketing copy is false.

## D-LLM-09 — Promote stable semantic patterns to rules

**Decision:** use the LLM for sampled semantic discovery; once a recurring pattern is human-validated, promote it to deterministic Rules vN.

**Status:** current.

**Reason:** the current corpus has only 12 description sentences, so permanent LLM inference over known patterns is hard to justify.

## D-LLM-10 — Preserve discovery/test separation

**Decision:** original 200-row sample becomes discovery-only; evaluate the post-discovery S001 rule on disjoint sets.

**Status:** current.

**Reason:** prevents design leakage after manually inspecting the discovery sample.
