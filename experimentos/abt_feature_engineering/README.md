# E016 — ABT + Feature Engineering point-in-time v1

## Objetivo

Construir una capa canónica y auditable de tratamiento de variables y tres ABTs de Lead Quality:

- **T0 — cold:** una fila por lead en `leads.created_at`.
- **T1 — first inquiry:** una fila por lead en su primera `inquiry_at`, antes de conocer respuesta del broker.
- **T2 — engaged:** una fila por segunda+ inquiry mientras todavía no haya ocurrido una visita agendada.

El target de los tres ABTs es:

`scheduled_visit observado en los siguientes 30 días desde score_time`.

Las filas sin 30 días completos de seguimiento se marcan como censuradas y se excluyen de los ABTs training-ready.

## Qué corrige respecto a pipelines genéricos

1. **Missing estructural por modalidad.** `sale` no recibe una mediana de renta y `rent` no recibe una mediana de venta. Se crean flags de aplicabilidad y los mínimos faltantes, cuando el presupuesto sí aplica, se interpretan como lower bound abierto (`0`) más un indicador explícito.
2. **Current-state leakage.** `days_on_market`, `total_inquiries`, `total_views` e `is_active` no entran crudos.
3. **`total_inquiries` se reconstruye as-of.** Se crea `spot_hist_prior_inquiries` desde `inquiries` usando sólo eventos anteriores al score.
4. **`broker_id` no se memoriza.** Se usa únicamente como llave para perfiles históricos point-in-time del broker.
5. **`broker_response_hours` se sanea semánticamente.** `no_response` con horas no se considera respuesta realizada. Un `response_event_at` sólo existe para `accepted/rejected/scheduled_visit` con tiempo observable.
6. **Availability usa backward as-of.** Nunca se selecciona un snapshot futuro.
7. **Land no aprende atributos de edificio sintéticamente extraños.** Los atributos built-environment se exponen como N/A para `sector_name=Land`; el valor fuente se preserva en el input original, no se reescribe.
8. **Amenities se parsea.** Se evita usar las 986 combinaciones JSON como una categoría única y se producen `amenities_count` + 12 flags multi-hot.
9. **Market Context queda fuera por defecto.** Sigue siendo `CONDITIONAL/UNKNOWN` hasta tener semántica de publicación/effective time.
10. **Texto se mantiene en sidecar semántico.** `title` y `description` no se usan crudos en el ABT principal.

## Archivos

- `feature_engineering.py`: contratos, transforms y joins point-in-time.
- `build_abts.py`: construcción T0/T1/T2 y escritura de outputs.
- `variable_treatment_manifest.csv`: tratamiento explícito de las 86 columnas originales.
- `LLM_FEATURE_ANALYSIS.md`: dónde sí/no puede ayudar un LLM.
- `tests/test_abt_builder.py`: pruebas de leakage y semántica crítica.
- `experiment_spec.json`: contrato de este experimento de preparación.

## Ejecución

```bash
pip install -r experimentos/abt_feature_engineering/requirements.txt
pytest -q experimentos/abt_feature_engineering/tests
python experimentos/abt_feature_engineering/build_abts.py --repo-root .
```

Outputs locales/CI:

- `results/abt_t0.parquet`
- `results/abt_t1.parquet`
- `results/abt_t2.parquet`
- muestras CSV de 200 filas por ABT
- `results/abt_summary.csv`
- `results/feature_sets.txt`

Los Parquet completos no deben versionarse si generan ruido innecesario; el código y los resúmenes son la fuente reproducible.

## Feature contracts por etapa

### T0

Lead intake únicamente: tipo de usuario, empresa, industria, necesidad inicial, modalidad, presupuestos tratados por aplicabilidad, geografía, source e historial previo declarado.

### T1

T0 + primera inquiry + spot estático + atributos físicos sector-aware + matching lead↔spot + disponibilidad backward-as-of + historial point-in-time del spot y broker.

### T2

T1 + trayectoria del propio lead: inquiries anteriores, spots distintos, requested/urgency/message trajectory y respuestas anteriores ya realizadas antes del nuevo score.

## Leakage policy

Cada lista de features se valida contra `BLOCKED_RAW_FEATURES`. Un modelo downstream debe consumir `feature_columns_for_stage(stage_id)` en vez de seleccionar columnas libremente.

`LEAKAGE_CHECK = PASS` para la arquitectura por diseño, condicionado a que las semánticas declaradas en las fuentes sigan siendo válidas. `market_context` no forma parte del feature set default.

## Estado

**IMPLEMENTED / NOT YET BENCHMARKED.**

Este experimento prepara el ABT canónico; no declara lift ni reemplaza la evaluación temporal de modelos existente hasta ejecutar challengers sobre estos ABTs.
