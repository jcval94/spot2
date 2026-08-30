# EV-027 — Broker prior point-in-time

**Estado:** evidencia empírica reproducible; mejora no demostrada.

**Experimento:** [E027](../feature_validation/E027_broker_prior_point_in_time/)

**GitHub Actions fuente:** https://github.com/jcval94/spot2/actions/runs/33281869820

## Resultado

El prior usa exclusivamente eventos de respuesta realizados estrictamente antes del scoring time y no usa `broker_id` como identidad predictiva.

Macro:

- baseline AP **0.5175**, AUC **0.5561**;
- broker prior AP **0.5190**, AUC **0.5578**.

Broker prior − baseline:

- ΔAP **+0.0015**, IC95% **[-0.0086, +0.0120]**;
- ΔAUC **+0.0018**, IC95% **[-0.0080, +0.0116]**.

T1 tiene un punto favorable:

- ΔAP **+0.0101**, IC95% **[-0.0148, +0.0371]**.

T2 tiene un punto desfavorable:

- ΔAP **-0.0075**, IC95% **[-0.0227, +0.0091]**.

## Interpretación

La gran dispersión descriptiva entre brokers no se transforma en lift predictivo robusto una vez el historial se construye correctamente point-in-time.

Eso sugiere que una parte relevante de las tasas brutas por broker provenía de composición de cartera, tiempo, geografía o inventario.

## Decisión

- no incluir broker prior en el release candidate del A/B definitivo;
- no cambiar routing de brokers basándose en esa tasa;
- si routing por broker sigue siendo una hipótesis de negocio, requiere un experimento causal específico.

## Evidencia fuente

- `E027_broker_prior_point_in_time/results/metrics_by_variant.csv`
- `E027_broker_prior_point_in_time/results/bootstrap_broker_prior_minus_baseline.csv`
- `E027_broker_prior_point_in_time/results/broker_prior_metrics_by_support.csv`
- harness record E027.


## Descubrimientos relacionados

- [D068](../conocimiento_agregado/DESCUBRIMIENTOS.md#d068--)
- [D074](../conocimiento_agregado/DESCUBRIMIENTOS.md#d074--)
