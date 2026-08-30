# E022 - Temporal feature ablation

## Hipotesis

Si el modelo esta dependiendo materialmente de clocks de cohorte/progreso, removerlos debe reducir desempeno fuera de tiempo.

**Conclusion: SUPPORTED.**

- Full - no-temporal AP: +0.0325.
- IC95% bootstrap por lead: [+0.0161, +0.0496].
- Time-proxy-only macro AUC: 0.596.
- Time-proxy-only macro AP: 0.549.

## Que se removio

- score_weekday
- score_hour
- score_month
- days_from_lead_creation
- inquiry_number
- days_since_first_inquiry

availability_snapshot_age_days se mantiene para no mezclar dos hipotesis; E023 lo audita aparte.

## Metricas

| Variante | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| full_reference | 0.556 | 0.517 | 0.245 | 0.684 | 1.12x | 0.220 |
| no_temporal | 0.512 | 0.485 | 0.250 | 0.693 | 1.00x | 0.202 |
| time_proxy_only | 0.596 | 0.549 | 0.245 | 0.682 | 1.23x | 0.248 |

## Lectura

Una variable temporal puede ser legitimamente observable y aun capturar drift. La pregunta aqui no es leakage, sino cuanto de la discriminacion depende de un reloj cuya distribucion cambia de cohorte a cohorte.
