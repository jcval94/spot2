# EV-012 — Trajectory / progression con rolling temporal CV

**Estado de evidencia:** empírica / final.

**Experimento:** [trajectory_cv](../modelo_3/trajectory_cv/)

**Parent:** [EV-011 — Rolling temporal CV de arquitectura](EV-011_modelo_3_architecture_cv.md)

## Diseño

E007 mantiene exactamente los cuatro folds temporales de E006 y cambia sólo el feature set.

Se añaden 19 features point-in-time:

- tiempo desde última inquiry;
- gap medio/desviación entre inquiries;
- velocidad de inquiries;
- tiempo desde última respuesta ya realizada;
- tiempo desde última aceptación ya observable;
- cobertura de respuestas históricas;
- inquiries previas todavía no resueltas;
- inquiries posteriores a última aceptación;
- diversidad/revisita de spots;
- repetición del spot actual;
- cambios de área;
- cambios de presupuesto de renta/venta;
- cambios de urgencia;
- cambios de longitud del mensaje;
- escalamiento de `asked_visit`;
- cambio de canal.

Las variables derivadas de respuesta sólo usan eventos con `response_event_at <= score_time`. La respuesta de la inquiry actual nunca entra como predictor.

## Evidencia fuente

- [Reporte](../modelo_3/trajectory_cv/results/REPORT.md)
- [Predicciones OOF](../modelo_3/trajectory_cv/results/oof_predictions.csv)
- [Métricas OOF](../modelo_3/trajectory_cv/results/oof_metrics.csv)
- [Métricas por fold](../modelo_3/trajectory_cv/results/fold_metrics.csv)
- [Bootstrap pareado](../modelo_3/trajectory_cv/results/paired_bootstrap.csv)
- [Ranking trajectory](../modelo_3/trajectory_cv/results/trajectory_model_ranking.csv)
- [Selección por fold](../modelo_3/trajectory_cv/results/fold_stage_selection.json)
- [Summary JSON](../modelo_3/trajectory_cv/results/summary.json)
- [Spec](../modelo_3/trajectory_cv/experiment_spec.json)
- [Harness record](harness_records/E007_trajectory_progression_cv/record.json)

## Resultado principal — T2 AP

| Familia | ΔAP trajectory vs baseline | IC95% | P(Δ>0) |
|---|---:|---:|---:|
| pooled CatBoost | +0.0161 | [+0.0003, +0.0322] | 97.9% |
| Multi-Head | +0.0155 | [+0.0013, +0.0303] | 98.2% |
| Random Forest | -0.0095 | [-0.0191, -0.0002] | 2.1% |
| specialist CatBoost | -0.0101 | [-0.0252, +0.0047] | 11.8% |

Para pooled CatBoost, T2 AUC también mejora +0.0117, IC95% [+0.0004, +0.0237].

Para Multi-Head, T2 AUC mejora +0.0176, IC95% [+0.0055, +0.0297].

## Resultado macro

| Modelo trajectory | ROC-AUC | AP | Brier | Log loss | Lift@10% |
|---|---:|---:|---:|---:|---:|
| trajectory validation hybrid | 0.5849 | 0.4764 | 0.2345 | 0.6608 | 1.21x |
| pooled CatBoost + trajectory | 0.5811 | 0.4752 | 0.2350 | 0.6618 | 1.24x |
| specialist CatBoost + trajectory | 0.5808 | 0.4705 | 0.2351 | 0.6623 | 1.23x |
| RF + trajectory | 0.5749 | 0.4678 | 0.2361 | 0.6643 | 1.18x |
| Multi-Head + trajectory | 0.5575 | 0.4549 | 0.2380 | 0.6683 | 1.14x |

La mejora macro de pooled CatBoost + trajectory frente a pooled CatBoost base es positiva (+0.0087 AP), pero su IC95% macro cruza cero. La evidencia robusta se concentra en T2.

## Interpretación

1. El concepto de trayectoria/progreso sí contiene señal incremental fuera de muestra.
2. La mejora depende de la arquitectura: pooled CatBoost y Multi-Head aprovechan el bloque; RF empeora.
3. No se debe trasladar feature engineering entre familias sin ablation.
4. Para una solución pragmática, `pooled CatBoost + stage + trajectory` queda como baseline operativo fuerte por simplicidad y desempeño; specialist CatBoost/RF siguen siendo challengers.

## Caveats

- El bloque de trajectory se probó completo; todavía falta una ablation por subfamilias para identificar qué componentes son necesarios.
- Las features de cambio requieren una inquiry previa y por diseño aportan principalmente en T2.
- El target continúa siendo `scheduled_visit`.
- Datos sintéticos; no hay interpretación causal.

## Descubrimientos

- [D035](../conocimiento_agregado/DESCUBRIMIENTOS.md#d035--la-trayectoria-explícita-aporta-señal-incremental-en-t2)
- [D036](../conocimiento_agregado/DESCUBRIMIENTOS.md#d036--trajectory-features-dependen-de-la-arquitectura)
- [D037](../conocimiento_agregado/DESCUBRIMIENTOS.md#d037--el-meta-selector-por-etapa-no-es-estable)
