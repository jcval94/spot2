# EV-020 — Lead Opportunity Score + Fallback end-to-end

**Estado de evidencia:** SUPPORTED / DECISION-READY.

**Experimento:** [E020_lead_opportunity_fallback_e2e](../E020_lead_opportunity_fallback_e2e/)

## Evidencia fuente

- [Reporte end-to-end](../E020_lead_opportunity_fallback_e2e/results/REPORT.md)
- [Selección de K](../E020_lead_opportunity_fallback_e2e/results/fallback_k_selection.csv)
- [Fallback fold 4](../E020_lead_opportunity_fallback_e2e/results/fallback_fold4_summary.csv)
- [Core metrics del proxy conjunto](../E020_lead_opportunity_fallback_e2e/results/joint_core_metrics.csv)
- [Métricas P85 por fold/stage](../E020_lead_opportunity_fallback_e2e/results/joint_capacity_metrics.csv)
- [Distribución del score](../E020_lead_opportunity_fallback_e2e/results/score_distribution_fold4.csv)
- [Diagnóstico de relevance histórico](../E020_lead_opportunity_fallback_e2e/results/behavioral_relevance_diagnostic.csv)
- [Summary](../E020_lead_opportunity_fallback_e2e/results/summary.json)
- [Runner reproducible](../E020_lead_opportunity_fallback_e2e/run_experiment.py)

## Fallback final

Política:

- hasta **K=3**;
- mismo sector;
- modalidad compatible;
- `spot.created_at <= score_time`;
- availability backward-as-of observable;
- área 0.5x–2.0x;
- precio total <=1.5x presupuesto;
- corredor -> municipio -> estado;
- no se cruza de estado;
- NO_RESULT cuando no existe alternativa defendible.

K se congela con folds 1–3:

- lista completa K3: **60.8%**;
- lista completa K5: **50.3%**.

Fold 4:

- 598 casos de fallback;
- coverage con >=1 recomendación en top-3: **75.9%**;
- lista completa de 3: **62.4%**;
- NO_RESULT: **24.1%**;
- al menos una alternativa actualmente disponible en top-3: **70.9%**;
- 86.1% de las recomendaciones devueltas están actualmente disponibles;
- 63.4% cumplen además el criterio estricto;
- cuando existen 3, 82.6% de las listas completas permanecen completamente en corredor.

## Relevance histórico: resultado negativo importante

El spot que orgánicamente termina en `scheduled_visit` no es un gold standard válido de recomendación:

- same sector: 67.4%;
- same corridor: 16.5%;
- strict policy: 1.0%;
- bounded policy: 1.75%.

Fold 4 behavioral Hit:

- Hit@1: 0%;
- Hit@3: 0%;
- Hit@5: 0.52%.

Esto se conserva; no se optimiza el fallback para imitar comportamiento que contradice las restricciones del assessment.

## Lead Opportunity Score

`LOS = P_quality × P_inventory_top3`

- Lead Quality: pooled CatBoost + stage + trajectory.
- Inventory: E019 P(availability) aplicada al spot actual + top-3 fallback.
- Se interpreta como score de oportunidad; no se declara independencia ni probabilidad conjunta perfectamente calibrada.

## Proxy operativo conjunto

`joint_success = scheduled_visit_30d AND confirmed_serviceable`

Confirmed serviceable:

- spot actual disponible as-of; o
- al menos una alternativa final top-3 disponible as-of.

Es una métrica de decisión, no un reemplazo del target de Lead Quality.

## Core metrics — joint_success

### T1

Quality-only -> LOS:

- AUC: **0.561 -> 0.652**;
- AP: **0.430 -> 0.487**;
- Brier: **0.237 -> 0.223**;
- Log-loss: **0.667 -> 0.636**;
- Lift@10%: **1.192x -> 1.281x**;
- Recall@20%: **21.7% -> 25.2%**.

### T2

- AUC: **0.623 -> 0.669**;
- AP: **0.394 -> 0.437**;
- Brier: **0.205 -> 0.197**;
- Log-loss: **0.597 -> 0.577**;
- Lift@10%: **1.432x -> 1.619x**;
- Recall@20%: **27.8% -> 32.1%**.

### Macro

- AUC: **0.592 -> 0.660**;
- AP: **0.412 -> 0.462**;
- Brier: **0.221 -> 0.210**;
- Log-loss: **0.632 -> 0.607**;
- Lift@10%: **1.312x -> 1.450x**;
- Recall@20%: **24.7% -> 28.7%**.

## P85 end-to-end — final fold

Misma capacidad operativa stage-relative:

- 219 snapshots seleccionados;
- joint positives quality-only: **106**;
- joint positives LOS: **114**;
- ganancia: **+8 / +7.5%**;
- confirmed-serviceable rate: **89.0% -> 100%**.

En el top P85 de Quality había 83 casos con spot actual no disponible; fallback encuentra una alternativa actualmente disponible para **59**, equivalente a ~**71.1%**.

## Guardrail de conversión pura

- conversion positives quality-only: **124**;
- conversion positives LOS: **114**;
- delta: **-10**.

Conclusión: LOS no sustituye Lead Quality si el objetivo es conversión pura. Sí es preferible cuando el objetivo declarado es conversión **y** serviceability.

## Leakage

- OOF temporal para Lead Quality;
- availability backward-as-of;
- spot future creation bloqueado;
- snapshot futuro bloqueado;
- current is_active bloqueado;
- scheduled_visit futuro sólo como outcome;
- fallback construido sólo con información disponible al score.

**LEAKAGE_CHECK = PASS**

## Qué demuestra

- fallback conceptual y @K están cerrados;
- existe fórmula final de Lead Opportunity Score;
- existe una evaluación conjunta con la misma capacidad operativa;
- el tradeoff conversión vs serviceability es explícito.

## Qué NO demuestra

- causalidad;
- que el spot histórico sea un relevance label de recomendación;
- impacto online;
- independencia de las probabilidades componentes.

Descubrimientos relacionados: D064–D067 en [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
