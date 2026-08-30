# EV-025 — Ablación de redundancias deterministas

**Estado:** evidencia empírica reproducible; no-inferioridad estricta inconclusa.

**Experimento:** [E025](../feature_validation/E025_redundancy_ablation/)

**GitHub Actions fuente:** https://github.com/jcval94/spot2/actions/runs/33281869820

## Resultado

Se eliminan `spot_price_total_mxn_rent` y `spot_price_total_mxn_sale`, manteniendo área, precio/m² y ratios de compatibilidad.

Macro:

- full: AUC **0.5561**, AP **0.5175**;
- sin price totals: AUC **0.5533**, AP **0.5198**.

No totals − full:

- ΔAP **+0.0023**, IC95% **[-0.0078, +0.0104]**;
- ΔAUC **-0.0028**, IC95% **[-0.01017, +0.00468]**.

El margen pre-registrado era -0.01 para AP y AUC. El límite inferior AUC queda apenas por debajo (-0.01017), así que bajo la regla fijada **no puede declararse formalmente no-inferior**.

## Interpretación

No hay evidencia de que los price totals aporten señal incremental importante; el punto AP incluso mejora al quitarlos. Pero no se debe cambiar retrospectivamente el margen para declarar éxito.

## Decisión

**INCONCLUSIVE bajo el contrato experimental.**

Por parsimonia son candidatos razonables a eliminar, pero el release final debe confirmarlo en otra cohorte o mantenerlos hasta esa confirmación.

## Evidencia fuente

- `E025_redundancy_ablation/results/metrics_by_variant.csv`
- `E025_redundancy_ablation/results/bootstrap_no_totals_minus_full.csv`
- harness record E025.


## Descubrimientos relacionados

- [D061](../conocimiento_agregado/DESCUBRIMIENTOS.md#d061--)
- [D072](../conocimiento_agregado/DESCUBRIMIENTOS.md#d072--)
