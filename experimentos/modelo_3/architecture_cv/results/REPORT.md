# Rolling temporal CV — arquitectura Modelo 3

**Conclusión pre-registrada tras CV: SUPPORTED.**

OOF: 7,980 snapshots, 1,936 leads, 4 folds temporales.

## Ranking OOF macro

| Modelo | AUC | AP | Brier | Log loss | Lift@10% |
|---|---:|---:|---:|---:|---:|
| Specialist CatBoost | 0.582 | 0.472 | 0.235 | 0.661 | 1.23x |
| Specialist Random Forest | 0.571 | 0.470 | 0.236 | 0.665 | 1.23x |
| Validation-selected hybrid | 0.573 | 0.468 | 0.236 | 0.664 | 1.20x |
| Pooled CatBoost + stage | 0.572 | 0.467 | 0.237 | 0.667 | 1.19x |
| Specialist LightGBM | 0.559 | 0.460 | 0.239 | 0.670 | 1.22x |
| Multi-Head | 0.550 | 0.450 | 0.239 | 0.670 | 1.13x |
| Specialist ExtraTrees | 0.543 | 0.447 | 0.239 | 0.671 | 1.13x |
| Pooled NN + stage | 0.548 | 0.445 | 0.239 | 0.670 | 1.13x |
| Separate Logistic | 0.499 | 0.415 | 0.262 | 0.728 | 0.99x |

## Replicación de hallazgos E005

- T1 RF vs Multi-Head ΔAP +0.034, IC95% [+0.011, +0.056].
- T1 RF vs Multi-Head ΔAUC +0.043, IC95% [+0.018, +0.069].
- pooled CatBoost vs Multi-Head macro ΔAUC +0.022, IC95% [+0.008, +0.037].
- pooled CatBoost vs Multi-Head macro ΔAP +0.017, IC95% [+0.002, +0.031].

## Regla

Este reporte completa la cross-validation requerida. El registro final de descubrimientos debe usar estos resultados, no el single holdout de E005 de forma aislada.
