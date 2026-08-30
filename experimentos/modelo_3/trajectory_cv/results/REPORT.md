# Trajectory / progression features — rolling temporal CV

**Conclusión: SUPPORTED.**

## Paired T2 Average Precision deltas

| Modelo + trajectory | Baseline | ΔAP | IC95% | P(Δ>0) |
|---|---|---:|---:|---:|
| pooled_catboost_trajectory | pooled_catboost_calibrated | +0.0161 | [+0.0003, +0.0322] | 97.9% |
| multihead_trajectory | multihead_calibrated | +0.0154 | [+0.0011, +0.0302] | 98.2% |
| specialist_random_forest_trajectory | specialist_random_forest_calibrated | -0.0095 | [-0.0191, -0.0002] | 2.1% |
| specialist_catboost_trajectory | specialist_catboost_calibrated | -0.0101 | [-0.0252, +0.0047] | 11.8% |

## Macro trajectory ranking

| Modelo | AUC | AP | Brier | Log loss | Lift@10% |
|---|---:|---:|---:|---:|---:|
| trajectory_validation_hybrid | 0.585 | 0.476 | 0.234 | 0.661 | 1.21x |
| pooled_catboost_trajectory | 0.581 | 0.475 | 0.235 | 0.662 | 1.24x |
| specialist_catboost_trajectory | 0.581 | 0.470 | 0.235 | 0.662 | 1.23x |
| specialist_random_forest_trajectory | 0.575 | 0.468 | 0.236 | 0.664 | 1.18x |
| multihead_trajectory | 0.557 | 0.455 | 0.238 | 0.668 | 1.14x |

## Leakage

Todas las variables response-derived usan exclusivamente respuestas de inquiries previas cuyo \`response_event_at <= score_time\`. La respuesta de la inquiry actual no se usa.

## Registro

Este experimento sólo debe promoverse a descubrimiento acumulado después de revisar conjuntamente E006 y E007.
