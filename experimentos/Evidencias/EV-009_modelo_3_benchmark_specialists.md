# EV-009 — Multi-Head vs especialistas tabulares

**Estado de evidencia:** empírica, comparación gobernada EQUIVALENT + bootstrap por lead.

**Experimento:** [benchmark_specialists](../modelo_3/benchmark_specialists/)

**Experimento padre:** [E003 / EV-003](EV-003_modelo_3_multihead.md)

## Evidencia fuente

- [Reporte](../modelo_3/benchmark_specialists/results/REPORT.md)
- [Métricas por etapa](../modelo_3/benchmark_specialists/results/metrics_by_stage.csv)
- [Ranking macro](../modelo_3/benchmark_specialists/results/model_ranking.csv)
- [Bootstrap vs Multi-Head](../modelo_3/benchmark_specialists/results/bootstrap_deltas_vs_multihead.csv)
- [Selección por validation](../modelo_3/benchmark_specialists/results/validation_stage_selection.json)
- [Scores de validation](../modelo_3/benchmark_specialists/results/validation_model_scores.csv)
- [Resumen JSON](../modelo_3/benchmark_specialists/results/summary.json)
- [Spec](../modelo_3/benchmark_specialists/experiment_spec.json)
- [Harness result](../modelo_3/benchmark_specialists/results/harness_results.json)

## Comparabilidad

El arnés clasificó E005 vs E003 como:

`COMPARISON_STATUS = EQUIVALENT`

Sin diferencias en scoring time, target, población, fuentes ni split temporal. El cambio primario es la familia/arquitectura de modelado.

Población test:

- 2,723 snapshots;
- 727 leads únicos;
- T0: 727;
- T1: 699;
- T2: 1,297.

## Ranking macro

| Modelo | AUC | AP | Brier | Log loss | Lift@10% |
|---|---:|---:|---:|---:|---:|
| validation-selected hybrid | 0.565 | 0.530 | 0.244 | 0.682 | 1.17x |
| pooled CatBoost + stage | 0.564 | 0.524 | 0.244 | 0.681 | 1.14x |
| specialist Random Forest | 0.556 | 0.517 | 0.245 | 0.684 | 1.12x |
| specialist CatBoost | 0.535 | 0.513 | 0.246 | 0.685 | 1.21x |
| specialist LightGBM | 0.548 | 0.511 | 0.248 | 0.689 | 1.11x |
| Multi-Head | 0.533 | 0.508 | 0.249 | 0.691 | 1.12x |

La conclusión gobernada del experimento es **INCONCLUSIVE** porque el mejor especialista fijo por macro AP, Random Forest, mejora +0.0092 pero su IC95% por lead es [-0.0173, +0.0394].

## Resultados que sí son robustos

### T1 — Random Forest especializado

- AP: 0.5628 vs 0.5075 Multi-Head.
- Delta AP: +0.0553.
- IC95%: [+0.0143, +0.0963].
- AUC: 0.5877 vs 0.4901.
- Delta AUC: +0.0975.
- IC95%: [+0.0523, +0.1439].

### Pooled CatBoost + stage — AUC macro

- AUC: 0.5642 vs 0.5330.
- Delta: +0.0312.
- IC95%: [+0.0076, +0.0573].
- P(delta > 0): 99.8%.

La mejora de AP macro del pooled CatBoost (+0.0159) no es robusta: IC95% [-0.0080, +0.0438].

## T2

Los mejores puntos fueron:

- Specialist CatBoost: AP 0.5338, AUC 0.6201.
- Specialist RF: AP 0.5213, AUC 0.6062.
- pooled CatBoost: AP 0.5203, AUC 0.6152.
- Multi-Head: AP 0.5148, AUC 0.5947.

Ningún delta T2 vs Multi-Head obtuvo IC95% completamente positivo. La arquitectura T2 sigue **INCONCLUSIVE**.

## Híbrido seleccionado sólo con validation

- T0 → Specialist CatBoost.
- T1 → Specialist Random Forest.
- T2 → pooled CatBoost + stage.

Test macro AP: 0.5295 vs 0.5083 Multi-Head; delta +0.0212, IC95% [-0.0059, +0.0520].

Es prometedor, pero no definitivo y tiene riesgo de selection bias por escoger entre varias familias usando el mismo validation set.

## Caveats

- Target proxy `scheduled_visit`, no outcome comercial oculto.
- Datos sintéticos.
- Los intervalos se obtienen remuestreando leads completos para conservar dependencia entre snapshots.
- El benchmark prueba varias familias; diferencias pequeñas se mantienen inconclusas.
- El híbrido requiere validación temporal adicional.

## Descubrimientos relacionados

- [D018 — no hay ganador global robusto por macro AP](../conocimiento_agregado/DESCUBRIMIENTOS.md#d018--no-hay-ganador-global-robusto-por-macro-ap)
- [D019 — T1 favorece Random Forest](../conocimiento_agregado/DESCUBRIMIENTOS.md#d019--t1-sí-necesita-un-challenger-más-fuerte-que-el-head-actual)
- [D020 — pooled CatBoost + stage](../conocimiento_agregado/DESCUBRIMIENTOS.md#d020--un-solo-modelo-fuerte-con-stage-puede-ser-suficiente-para-buena-discriminación)
- [D021 — T2 sin ganador robusto](../conocimiento_agregado/DESCUBRIMIENTOS.md#d021--t2-mantiene-señal-pero-no-un-ganador-de-arquitectura)
- [D022 — híbrido prometedor](../conocimiento_agregado/DESCUBRIMIENTOS.md#d022--el-híbrido-por-etapa-es-prometedor-todavía-no-definitivo)
