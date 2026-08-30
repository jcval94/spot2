# E027 - Point-in-time broker prior

**Conclusion: INCONCLUSIVE.**

- Broker prior - baseline AP: +0.0015.
- IC95% bootstrap por lead: [-0.0086, +0.0120].

El prior no usa broker_id como identidad categorica. Solo usa historial ya realizado antes del score: volumen de respuestas, scheduled visits previas y una tasa suavizada.

| Variante | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| full_no_broker_prior | 0.556 | 0.517 | 0.245 | 0.684 | 1.12x | 0.220 |
| broker_prior | 0.558 | 0.519 | 0.246 | 0.684 | 1.08x | 0.227 |

Incluso una mejora predictiva no probaria que reasignar un lead a ese broker cause mayor conversion; eso requeriria diseno de routing/experimento.
