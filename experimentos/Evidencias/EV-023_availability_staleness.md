# EV-023 — Availability staleness

**Estado:** evidencia empírica reproducible.

**Experimento:** [E023](../feature_validation/E023_availability_staleness/)

**GitHub Actions fuente:** https://github.com/jcval94/spot2/actions/runs/33281869820

## Resultado

La edad cruda del snapshot no muestra utilidad robusta.

Macro AP:

- raw age: **0.5175**;
- drop raw age: **0.5236**;
- guarded staleness: **0.5173**.

Drop raw age − raw age:

- ΔAP **+0.0061**, IC95% **[-0.0048, +0.0166]**.

Guarded − raw:

- ΔAP **-0.0002**, IC95% **[-0.0089, +0.0089]**.

La representación protegida cumple el margen pre-registrado de no-inferioridad de -0.01 AP.

## Interpretación

`availability_snapshot_age_days` no debe tratarse como una señal comercial tipo “más viejo = mejor/peor”. E021 mostró además drift fuerte en esa variable.

La frescura sí es importante como **calidad/serviciabilidad de la información**. Por eso se separa:

- estado de availability;
- freshness;
- unknown cuando el snapshot histórico supera 90 días.

## Decisión

Para el sistema causal:

- eliminar la edad cruda como predictor;
- conservar freshness/staleness como guardrail o representación explícita;
- >90d = estado histórico desconocido, nunca “available” por default;
- producción debe preferir inventario live/current.

## Evidencia fuente

- `E023_availability_staleness/results/metrics_by_variant.csv`
- `E023_availability_staleness/results/bootstrap_delta_vs_raw_age.csv`
- `E023_availability_staleness/results/metrics_by_snapshot_age_bucket.csv`
- harness record E023.


## Descubrimientos relacionados

- [D064](../conocimiento_agregado/DESCUBRIMIENTOS.md#d064--)
- [D070](../conocimiento_agregado/DESCUBRIMIENTOS.md#d070--)
