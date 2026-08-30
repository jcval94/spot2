# E020 — Lead Opportunity Score + Fallback end-to-end

## Objetivo

Cerrar los cuatro gaps restantes del assessment:

1. fallback conceptual;
2. fallback final evaluado @K;
3. Lead Opportunity Score combinado;
4. evaluación end-to-end del sistema combinado.

## Decisión final

### Fallback

El sistema devuelve **hasta K=3 alternativas** cuando el spot actual no está confirmado como disponible en el último snapshot conocido al momento del score.

Hard constraints:

- mismo sector del lead;
- modalidad compatible;
- spot ya existente en `score_time`;
- snapshot de availability observable con `snapshot_date <= score_time`.

Relajación acotada:

1. corredor preferido;
2. municipio preferido;
3. estado preferido;
4. nunca cruza de estado.

Viabilidad:

- área del spot entre 0.5x y 2.0x del área solicitada/objetivo;
- precio total <= 1.5x del presupuesto máximo relevante;
- ranking final por geografía, disponibilidad actual y distancia logarítmica de área + precio/m².

Si no existe candidato que cumpla esos límites, el sistema devuelve **NO_RESULT** en vez de recomendar un inmueble poco defendible.

### Lead Opportunity Score

`Lead Opportunity Score = P_quality × P_inventory_top3`

donde:

- `P_quality` = `pooled_catboost_trajectory` OOF;
- `P_inventory_top3` = máximo entre la probabilidad de disponibilidad del spot actual y las probabilidades de las alternativas top-3;
- las probabilidades de inventory reutilizan E019.

El producto se trata como **score de oportunidad**, no como probabilidad conjunta perfectamente calibrada, porque no se asume independencia entre los dos componentes.

## Evaluación

La conversión pura sigue siendo un guardrail.

La evaluación principal del sistema combinado usa el proxy operativo:

`joint_success = scheduled_visit_30d AND confirmed_serviceable`

`confirmed_serviceable` significa que el spot actual o al menos una recomendación top-3 está disponible en el snapshot as-of.

Esto evalúa la decisión de negocio que el Lead Opportunity Score intenta tomar: priorizar leads que además de convertir, pueden ser atendidos.

Ver [results/REPORT.md](results/REPORT.md).
