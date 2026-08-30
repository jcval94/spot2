# EV-022 — Ablación de variables temporales/progreso

**Estado:** evidencia empírica reproducible; hallazgo crítico para release.

**Experimento:** [E022](../feature_validation/E022_temporal_feature_ablation/)

**GitHub Actions fuente:** https://github.com/jcval94/spot2/actions/runs/33281869820

## Pregunta

¿Cuánto del desempeño del Random Forest especialista de E005 depende de clocks de calendario/progreso sujetos a drift?

Se retiran:

- `score_weekday`;
- `score_hour`;
- `score_month`;
- `days_from_lead_creation`;
- `inquiry_number`;
- `days_since_first_inquiry`.

## Resultado principal

**SUPPORTED: una fracción material de la señal depende de esas variables.**

Macro:

| Variante | AUC | AP | Lift@10% |
|---|---:|---:|---:|
| RF completo | 0.5561 | 0.5175 | 1.116x |
| sin temporal/progreso | 0.5122 | 0.4850 | 1.001x |
| time-proxy-only diagnóstico | **0.5960** | **0.5492** | **1.233x** |

Full − no-temporal:

- ΔAP **+0.0325**, IC95% **[+0.0161, +0.0496]**;
- ΔAUC **+0.0439**, IC95% **[+0.0257, +0.0625]**.

T1 es el caso más fuerte:

- RF completo AUC **0.5877**, AP **0.5628**;
- sin clocks AUC **0.5038**, AP **0.5097**;
- ΔAUC **+0.0839**, IC95% **[+0.0494, +0.1208]**;
- ΔAP **+0.0531**, IC95% **[+0.0200, +0.0815]**.

T2 conserva algo más de señal después de la ablación:

- AUC **0.5736**;
- AP **0.4912**;
- Lift@10% **1.176x**.

## Interpretación

Este resultado **refina fuertemente D019**.

E005 demostró correctamente que el RF especialista T1 extraía más señal que el Multi-Head, pero E022 muestra que gran parte de esa señal no sobrevive al retirar clocks/progreso. Por tanto, no debe interpretarse como evidencia de intención T1 estable.

El hallazgo más preocupante es que el modelo `time-proxy-only` supera al RF completo en macro AUC/AP. Eso es coherente con el fuerte drift de E021 y con el proceso sintético.

## Decisión

El release candidate para un A/B causal **no puede usar sin más la versión E005 con clocks crudos**.

Antes de producción se requiere una versión drift-sanitized y una validación en cohorte futura. En particular, el especialista T1 de E005 queda bloqueado como candidato de producción mientras su señal dependa de esas variables.

## No demuestra

- no prueba que tiempo no tenga ningún valor real;
- no obliga a ignorar recencia operativa en reglas de producto;
- no invalida T2 ni la historia observable completa;
- no prueba que un modelo sin clocks ya sea suficientemente bueno para producción.

## Evidencia fuente

- `E022_temporal_feature_ablation/results/metrics_by_variant.csv`
- `E022_temporal_feature_ablation/results/bootstrap_full_minus_no_temporal.csv`
- `E022_temporal_feature_ablation/results/summary.json`
- harness record E022.


## Descubrimientos relacionados

- [D069](../conocimiento_agregado/DESCUBRIMIENTOS.md#d069--)
- [D075](../conocimiento_agregado/DESCUBRIMIENTOS.md#d075--)
