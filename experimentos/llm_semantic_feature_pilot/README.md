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

## Estado actual

**READY_FOR_100_API_PILOT / API KEY NOT AVAILABLE IN CURRENT RUNTIME.**

No existe todavía un resultado LLM real y no se simula uno. El archivo final sólo debe llamarse `pilot_llm_results_100.csv` después de una respuesta real de la API.
