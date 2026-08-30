# Plan — LLM Inventory Semantic Quality

## Decisión de arquitectura antes de implementar

La primera implementación debe usar **OpenAI Responses API directamente**, con salida estructurada validada en Python.

No se propone inicialmente:

- Google ADK;
- LangChain/LangGraph;
- OpenAI Agents SDK;
- un agente con tools o memoria.

La tarea es corta, stateless y acotada: recibe una ficha y devuelve un audit estructurado. Un runtime agentic añadiría orquestación que todavía no existe en el problema.

El acceso se configurará con el secret `OPENAIAPI`, aceptando opcionalmente `OPENAI_API_KEY` como fallback local. El modelo se mantendrá configurable; no se fijará un ganador antes de validarlo.

## Pregunta experimental

¿Un LLM detecta inconsistencias semánticas materialmente útiles entre `title/description` y los atributos estructurados del inmueble que un baseline razonable de reglas no detecta?

## Hipótesis

**H1:** Rules + LLM aumenta la cobertura/recall de inconsistencias relevantes frente a Rules-only sin degradar excesivamente precision.

**H0 / criterio de descarte:** el lenguaje es tan repetitivo y sintético que reglas de alta precisión capturan prácticamente todos los problemas; el LLM añade falsos positivos, costo o poca cobertura incremental.

## Fase 0 — Taxonomía y auditoría de texto

Antes de llamar a la API:

1. perfilar frases y n-grams recurrentes de `title` y `description`;
2. cuantificar duplicación/repetición de copy;
3. definir una taxonomía de claims verificables;
4. separar contradicciones verificables de juicios subjetivos.

Taxonomía inicial:

- `natural_light`;
- `security`;
- `parking`;
- `building_condition/readiness`;
- `amenities`;
- `accessibility/access` cuando exista un campo estructurado comparable;
- `semantic_implausibility` como categoría separada y no crítica por defecto.

## Fase 1 — Baseline determinístico

Construir primero reglas explícitas de alta precisión.

Ejemplos:

- claim de iluminación natural + `natural_light=false`;
- claim de seguridad + `security_type=none`;
- claim explícito de estacionamiento + `parking_spaces=0` y sin amenity equivalente;
- “listo para ocupar / recién remodelado” + `building_status=needs_renovation`.

El baseline debe registrar:

- regla disparada;
- evidencia textual;
- campo estructurado;
- valor observado;
- severidad.

El LLM sólo se evalúa después de tener este baseline.

## Fase 2 — Gold standard humano

No usar otro LLM como juez principal.

Construir una muestra estratificada revisada manualmente, con representación de:

- listings sin reglas disparadas;
- listings con reglas disparadas;
- distintos sectores/tipos;
- distintas combinaciones de frases;
- casos potencialmente ambiguos.

Cada listing recibe labels a nivel claim:

- `consistent`;
- `contradiction`;
- `unsupported_claim`;
- `ambiguous`;
- `not_verifiable`.

La guía de etiquetado debe quedar versionada.

## Fase 3 — Auditor LLM

Para cada listing, enviar únicamente los campos necesarios y pedir Structured Output.

El modelo debe:

1. extraer claims del texto;
2. citar evidencia textual;
3. mapearlos a atributos verificables;
4. comparar sólo contra datos proporcionados;
5. abstenerse si no existe evidencia estructurada suficiente.

No debe usar conocimiento externo para afirmar hechos sobre una ubicación o inmueble.

## Fase 4 — Comparación

Comparar sobre el mismo holdout humano:

### A — Rules only

Baseline determinístico.

### B — LLM only

Auditor semántico.

### C — Rules + LLM

Reglas de alta precisión primero; LLM aporta detecciones adicionales.

Métricas principales:

- precision de contradicciones;
- recall;
- F1;
- false-positive rate;
- incremental recall de C vs A;
- número/tipo de issues encontrados sólo por LLM;
- tasa de abstención;
- schema-valid response rate.

Métricas operativas:

- tokens por listing;
- costo por 1,000 listings;
- latencia p50/p95;
- retry/error rate;
- cache hit rate.

## Fase 5 — Criterio de go/no-go

El LLM sólo avanza hacia integración si demuestra simultáneamente:

1. precisión alta en flags críticos sobre labels humanos;
2. cobertura incremental material sobre Rules-only;
3. errores de schema y ejecución bajos;
4. costo/latencia razonables para un audit de catálogo;
5. categorías adicionales que puedan convertirse en una acción real de revisión.

Umbrales concretos se congelarán antes del holdout final. Como punto de partida para validation se propone explorar:

- precision >= 0.90 en `critical contradiction`;
- incremental recall >= 10 pp frente a Rules-only, o una nueva categoría de issues con precision >= 0.85;
- schema-valid >= 99%.

Estos valores son **criterios de diseño preliminares**, no resultados.

## Fase 6 — Integración de negocio, sólo si pasa

Primera integración permitida:

```text
listing
  -> structured checks
  -> semantic quality audit
  -> GOOD / REVIEW / CRITICAL
  -> catalog QA queue
```

No alterar automáticamente el Lead Opportunity Score.

Después, y sólo con evidencia suficiente, evaluar como guardrail:

```text
candidate inventory
  -> eligibility / availability
  -> semantic-quality gate
  -> fallback ranking
```

## Reproducibilidad y costo

- El workflow LIVE será manual, no en cada push.
- Cachear respuestas por hash del input + prompt + model.
- CI normal utilizará replay de outputs guardados cuando sea necesario.
- Nunca persistir la API key.
- Registrar modelo, prompt version/hash, response id, token usage y resultado parseado.
- El secret GitHub se llamará `OPENAIAPI`.

## Resultado esperado del experimento

El resultado válido puede ser cualquiera de estos:

- **SUPPORTED:** el LLM añade cobertura útil con precisión suficiente;
- **NOT_SUPPORTED:** reglas resuelven el problema de forma más simple;
- **INCONCLUSIVE:** el labeled set o la ambigüedad del copy no permite decidir.

El uso obligatorio de IA del assessment no justifica maquillar un resultado negativo.
