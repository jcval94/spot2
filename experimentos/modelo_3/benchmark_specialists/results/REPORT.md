# Multi-Head vs especialistas tabulares

## Respuesta

**Conclusión gobernada: INCONCLUSIVE.**
El mejor especialista fijo por macro AP fue **Specialist Random Forest**: AP 0.517 vs 0.508 del Multi-Head (delta +0.009).
Bootstrap por lead para ese delta: IC95% [-0.017, +0.039], P(delta>0)=76.0%.

## Ranking macro

| Modelo | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| Validation-selected hybrid | 0.565 | 0.530 | 0.244 | 0.682 | 1.17x | 0.227 |
| Pooled CatBoost + stage | 0.564 | 0.524 | 0.244 | 0.681 | 1.14x | 0.230 |
| Specialist Random Forest | 0.556 | 0.517 | 0.245 | 0.684 | 1.12x | 0.220 |
| Specialist CatBoost | 0.535 | 0.513 | 0.246 | 0.685 | 1.21x | 0.223 |
| Specialist LightGBM | 0.548 | 0.511 | 0.248 | 0.689 | 1.11x | 0.222 |
| Multi-Head | 0.533 | 0.508 | 0.249 | 0.691 | 1.12x | 0.221 |
| Separate Logistic | 0.503 | 0.499 | 0.281 | 0.768 | 1.10x | 0.218 |
| Pooled NN + stage | 0.527 | 0.497 | 0.249 | 0.692 | 1.08x | 0.206 |
| Specialist ExtraTrees | 0.512 | 0.494 | 0.250 | 0.694 | 1.10x | 0.205 |

## Average Precision por etapa

| Modelo | T0 | T1 | T2 |
|---|---:|---:|---:|
| Validation-selected hybrid | 0.505 | 0.563 | 0.520 |
| Pooled CatBoost + stage | 0.507 | 0.545 | 0.520 |
| Specialist Random Forest | 0.468 | 0.563 | 0.521 |
| Specialist CatBoost | 0.505 | 0.500 | 0.534 |
| Specialist LightGBM | 0.482 | 0.555 | 0.498 |
| Multi-Head | 0.503 | 0.508 | 0.515 |
| Separate Logistic | 0.498 | 0.510 | 0.488 |
| Pooled NN + stage | 0.511 | 0.503 | 0.476 |
| Specialist ExtraTrees | 0.478 | 0.518 | 0.487 |

## Modelo elegido por validation para cada etapa

- **T0_cold:** Specialist CatBoost.
- **T1_first_inquiry:** Specialist Random Forest.
- **T2_engaged:** Pooled CatBoost + stage.

El híbrido usa esa selección sin mirar test. Aun así, es una selección entre varias familias sobre el mismo validation set, por lo que debe interpretarse como una arquitectura candidata y no como una estimación libre de selection bias.

## Lectura arquitectónica

- Si un pooled CatBoost fuerte iguala o supera al multi-head, la ventaja de E003 puede provenir parcialmente de que el challenger pooled original era débil, no necesariamente de necesitar heads.
- Si los especialistas ganan sólo en T2, la arquitectura más razonable es híbrida: compartir un esquema de scoring, pero permitir un especialista tabular para la etapa engaged.
- Si el Multi-Head gana de forma robusta en macro AP y en T2, entonces el shared backbone conserva evidencia a favor incluso frente a challengers tabulares fuertes.

## Controles

- Misma construcción point-in-time de E003.
- Misma ventana futura de 30 días y mismo censoring.
- Mismo split temporal por lead; ningún lead cruza train/validation/test.
- Validation se usa para early stopping, calibración y selección del híbrido.
- El bootstrap remuestrea leads completos para respetar la dependencia entre snapshots de un mismo lead.

## Caveats

- scheduled_visit sigue siendo un proxy, no la etiqueta final oculta.
- Los datos son sintéticos.
- Se prueban varias familias; el híbrido puede sobreajustarse al validation set.
- Diferencias pequeñas con IC95% que cruza cero se consideran inconclusas.

## Siguiente paso

Si aparece un ganador robusto por etapa, el siguiente experimento debe hacer feature engineering de trayectoria/progreso únicamente sobre ese ganador y medir lift incremental contra este benchmark congelado.
