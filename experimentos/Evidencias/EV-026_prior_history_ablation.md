# EV-026 — prior_searches vs prior_inquiries

**Estado:** evidencia empírica reproducible.

**Experimento:** [E026](../feature_validation/E026_prior_history_ablation/)

**GitHub Actions fuente:** https://github.com/jcval94/spot2/actions/runs/33281869820

## Resultado

La hipótesis de que ambas variables aportan señal incremental útil **no se sostiene**.

Macro AP:

- full: **0.5175**;
- drop prior_searches: **0.5276**;
- drop prior_inquiries: **0.5236**;
- drop both: **0.5239**.

Para `prior_searches`, full − drop:

- ΔAP **-0.0101**, IC95% **[-0.0183, -0.0010]**.

Es decir, quitar `prior_searches` mejora AP de forma robusta en este holdout.

En T0:

- full AP **0.4683**;
- sin prior_searches AP **0.4864**.

Para `prior_inquiries`, full − drop:

- ΔAP **-0.0061**, IC95% **[-0.0152, +0.0025]**.

El punto también favorece eliminarla, pero el intervalo cruza cero.

## Interpretación

Que `prior_searches` y `prior_inquiries` sean casi incorreladas no implica que ambas sean útiles. La primera está comportándose como una feature perjudicial/inestable para este RF congelado.

## Decisión

- retirar `prior_searches` del release candidate actual;
- `prior_inquiries`: utilidad incremental no demostrada; preferir parsimonia y someter su inclusión a validación futura;
- no crear un engagement score sumando ambas.

## Evidencia fuente

- `E026_prior_history_ablation/results/metrics_by_variant.csv`
- `E026_prior_history_ablation/results/bootstrap_full_minus_ablation.csv`
- harness record E026.


## Descubrimientos relacionados

- [D067](../conocimiento_agregado/DESCUBRIMIENTOS.md#d067--)
- [D073](../conocimiento_agregado/DESCUBRIMIENTOS.md#d073--)
