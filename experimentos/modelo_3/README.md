# Modelo 3 — scoring dinámico por etapa

> **Estado actual:** este directorio nació como experimento Multi-Head, pero E005–E007 muestran que el Multi-Head ya no es la arquitectura líder. La decisión actual está en [DECISION_ARQUITECTURA.md](DECISION_ARQUITECTURA.md). El código original se conserva como baseline y evidencia histórica.
>
> El proceso completo, incluyendo cambios de criterio, incidencias y cierre formal, está en [registro_flujo/modelo_3](../registro_flujo/modelo_3/).


Este experimento prueba una arquitectura supervisada dinámica para \`Lead Quality\` en Spot2. En vez de entrenar un único clasificador con \`stage\` como una columna, el modelo aprende una **representación compartida** y usa una salida distinta para cada momento del funnel.

## Arquitectura

- **Backbone compartido:** MLP \`input -> 128 -> 64\`.
- **Head T0 — cold:** score al crear el lead.
- **Head T1 — first inquiry:** score cuando llega la primera consulta, antes de conocer la respuesta del broker.
- **Head T2 — engaged:** score desde la segunda consulta en adelante, siempre que todavía no haya ocurrido una visita agendada.
- **Target móvil:** \`scheduled_visit\` futuro dentro de 30 días **desde el timestamp de scoring de cada fila**.
- **Calibración:** Platt scaling independiente por head usando exclusivamente validación.

La misma corrida compara tres alternativas:

1. \`multihead_calibrated\`: backbone compartido + tres heads. **Baseline histórico de E003; ya no es la recomendación final tras E006/E007.**
2. \`pooled_calibrated\`: un solo modelo que recibe \`stage\` como one-hot. Challenger directo a la pregunta "¿basta con una variable de etapa?".
3. \`separate_logistic\`: tres regresiones logísticas independientes. Baseline de baja complejidad.

## Por qué T2 usa varias filas por lead

T2 representa un sistema de re-scoring real: un lead involucrado puede volver a puntuarse en cada nueva inquiry. Para evitar que los usuarios muy activos dominen el entrenamiento, el loss pondera las filas para equilibrar etapas y repartir el peso dentro de cada combinación lead-etapa.

Todos los snapshots de un mismo lead permanecen en el mismo cohort de train/validation/test.

## Controles de leakage

El experimento aplica explícitamente reglas point-in-time:

- bloquea \`lead_score_internal\`;
- no usa la respuesta actual/futura del broker como feature;
- para historial de respuestas sólo usa respuestas cuyo timestamp inferido (\`inquiry_at + broker_response_hours\`) ya ocurrió al momento del score;
- excluye \`spots.days_on_market\`, \`total_inquiries\`, \`total_views\` e \`is_active\`, porque son snapshots potencialmente posteriores;
- une disponibilidad con el último \`availability_snapshot\` **a o antes** del timestamp de scoring;
- elimina observaciones censuradas sin 30 días futuros completos;
- elimina scores posteriores a una visita ya ocurrida.

El \`broker_response_hours\` no se usa como predictor del evento actual: sólo sirve para reconstruir cuándo una respuesta histórica ya era observable.

## Features

### Compartidas desde T0

Tipo de usuario, tamaño de empresa, industria, sector/modalidad de búsqueda, área, presupuestos, geografía preferida, fuente e historial previo declarado en \`leads\`.

### Disponibles desde T1

Canal, \`asked_visit\`, longitud del mensaje, área y presupuesto solicitados, urgencia, tiempo desde creación del lead, atributos estáticos del spot, compatibilidad lead↔spot y disponibilidad point-in-time.

### Acumuladas en T2

Número de inquiries previas, spots distintos, tasa previa de \`asked_visit\`, medias históricas de mensaje/urgencia y respuestas del broker ya conocidas a ese timestamp.

## Validación

La separación es cronológica por \`leads.created_at\`: 70% train, 15% validación y 15% test. La unidad de aislamiento es el **lead**, no la fila de scoring, para impedir que T0 de un lead esté en train y T2 del mismo lead en test.

Métricas por head y macro:

- ROC-AUC
- Average Precision
- Brier score
- Log loss
- Lift@10%
- Recall@20%

## Decisión del experimento

El arnés clasifica el resultado como:

- \`SUPPORTED\` si multi-head mejora de forma material Average Precision frente al pooled sin degradar materialmente ROC-AUC;
- \`NOT_SUPPORTED\` si pierde claramente en ambas;
- \`INCONCLUSIVE\` si quedan prácticamente empatados.

La decisión se basa en el conjunto de test; no se usa test para early stopping ni calibración.

## Ejecución local

\`\`\`bash
pip install -r experimentos/modelo_3/requirements.txt
python experimentos/_sistema/harness/experiment_harness.py validate \
  --spec experimentos/modelo_3/experiment_spec.json \
  --repo-root .
python experimentos/modelo_3/run_experiment.py
python experimentos/_sistema/harness/experiment_harness.py finalize \
  --spec experimentos/modelo_3/experiment_spec.json \
  --results experimentos/modelo_3/results/harness_results.json \
  --repo-root . \
  --output-dir experimentos/Evidencias/harness_records
\`\`\`

## Outputs

Persistidos en el repo por GitHub Actions cuando corre en \`main\`:

- \`results/summary.md\`
- \`results/summary.json\`
- \`results/metrics_by_stage.csv\`
- \`results/population_by_stage.csv\`
- \`results/calibration.json\`
- histories de entrenamiento
- \`results/harness_results.json\`

Disponibles sólo como artifact del workflow:

- \`experimentos/modelo_3/artifacts/multihead_model.pt\`
- \`experimentos/modelo_3/artifacts/test_predictions.csv\`
- registro final del experiment harness

## Limitación principal

\`scheduled_visit\` es un proxy supervisado observable, no el outcome final oculto del assessment. El resultado decide cuál arquitectura describe mejor este dataset sintético; no demuestra causalidad sobre cómo mover leads entre etapas.


## Evolución posterior

- [benchmark_specialists/](benchmark_specialists/) — E005, challengers tabulares fuertes.
- [architecture_cv/](architecture_cv/) — E006, rolling temporal CV que confirma la ventaja de modelos tabulares.
- [trajectory_cv/](trajectory_cv/) — E007, trajectory/progression features bajo los mismos folds.
- [DECISION_ARQUITECTURA.md](DECISION_ARQUITECTURA.md) — recomendación consolidada actual.

La evidencia central final está en [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md) y [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md).
