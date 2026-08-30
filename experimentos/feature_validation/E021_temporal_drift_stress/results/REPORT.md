# E021 - Temporal drift stress test

## Pregunta

El proceso y el rendimiento del modelo son estables a traves del tiempo, o una parte material de la senal esta asociada al regimen/cohorte?

## Resultado

**Conclusion: SUPPORTED.**

- Rango de positive rate macro entre folds: 0.124.
- Rango de ROC-AUC macro: 0.018.
- PSI maximo early vs late: 2.824.
- PSI mediano: 0.006.

El punto importante no es que una metrica cambie por si sola: el target, variables de progreso y el regimen de interaccion se desplazan simultaneamente. Por eso cualquier modelo que use clocks de funnel debe validarse fuera de tiempo y por cohortes.

## OOF metrics

| Variante | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| rolling_rf | 0.577 | 0.475 | 0.237 | 0.666 | 1.23x | 0.244 |

## Por que importa

Un feature puede ser perfectamente point-in-time y aun asi ser peligroso: puede aprender cuando fue generado el dato en lugar de una relacion estable con la intencion comercial. Eso no es leakage clasico, pero si riesgo de generalizacion.

## Evidencia

- fold_metrics.csv
- cohort_target_rates.csv
- feature_psi_early_vs_late.csv
- drift_summary.json
- charts/cohort_target_rate.png
- charts/feature_psi.png
