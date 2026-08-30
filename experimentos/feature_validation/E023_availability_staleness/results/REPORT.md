# E023 - Availability staleness

**Conclusion: SUPPORTED.**

La version protegida reemplaza la edad cruda por log-age + bucket y trata snapshots >90 dias como contexto de disponibilidad desconocido.

- Guarded - raw AP: -0.0002.
- IC95%: [-0.0089, +0.0089].
- Margen de no inferioridad declarado: -0.010 AP.

## Metricas

| Variante | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| full_raw_age | 0.556 | 0.517 | 0.245 | 0.684 | 1.12x | 0.220 |
| drop_raw_age | 0.559 | 0.524 | 0.245 | 0.683 | 1.08x | 0.230 |
| guarded_staleness | 0.552 | 0.517 | 0.245 | 0.684 | 1.05x | 0.220 |

## Por que

E020 mostro gaps de snapshots de hasta 319 dias. Una fecha de snapshot anterior al score hace la feature legal point-in-time, pero no necesariamente confiable. La representacion protegida separa availability de freshness.
