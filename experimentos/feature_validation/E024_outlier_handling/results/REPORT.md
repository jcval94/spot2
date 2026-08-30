# E024 - Outlier handling

## Hipotesis

Eliminar del entrenamiento el 3% de casos mas anomalos, definidos sin outcome, deberia mejorar generalizacion si realmente son ruido perjudicial.

**Conclusion: INCONCLUSIVE.**

- Train rows eliminadas: 436 (3.11%).
- Drop - keep AP: +0.0063.
- IC95%: [-0.0029, +0.0143].

## Metricas

| Variante | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| keep_all | 0.556 | 0.517 | 0.245 | 0.684 | 1.12x | 0.220 |
| drop_train_anomalies | 0.559 | 0.524 | 0.245 | 0.683 | 1.10x | 0.225 |
| anomaly_indicator | 0.559 | 0.522 | 0.245 | 0.684 | 1.08x | 0.224 |

El test permanece intacto. Por tanto, si borrar anomalies no mejora, no existe respaldo predictivo para limpiar esas filas solo por rareza.
