# E006 — Confirmación arquitectónica con rolling temporal CV

## Objetivo

Repetir E005 sin registrar una nueva conclusión arquitectónica a partir de un solo holdout.

La comparación se rehace con **rolling-origin cross-validation temporal por lead**. Cada lead pertenece a un único bloque temporal de test por fold y nunca aparece simultáneamente en train/validation/test dentro del mismo fold.

## Diseño

Se usan cuatro folds forward-chaining sobre leads ordenados por `created_at`:

- Fold 1: train 0–45%, validation 45–55%, test 55–65%.
- Fold 2: train 0–55%, validation 55–65%, test 65–75%.
- Fold 3: train 0–65%, validation 65–75%, test 75–85%.
- Fold 4: train 0–75%, validation 75–85%, test 85–95%.

Los test cohorts son disjuntos y producen predicciones out-of-fold (OOF).

## Modelos

Se repite el set de challengers de E005:

- Multi-Head;
- pooled neural + stage;
- Logistic por etapa;
- Random Forest por etapa;
- ExtraTrees por etapa;
- LightGBM por etapa;
- CatBoost por etapa;
- pooled CatBoost + stage;
- híbrido seleccionado dentro de cada fold usando sólo validation.

## Decisión

La evidencia primaria será:

1. métricas OOF agregadas;
2. consistencia fold a fold;
3. bootstrap por `lead_id` sobre las predicciones OOF.

No se actualizará una conclusión final en conocimiento agregado hasta completar esta CV.


## Resultado final

E006 terminó correctamente con 4 folds temporales, 7,980 snapshots OOF y 1,936 leads.

La conclusión gobernada es **SUPPORTED**:

- Specialist CatBoost: macro AP 0.4720, AUC 0.5820.
- Specialist Random Forest: macro AP 0.4698, AUC 0.5711.
- pooled CatBoost + stage: macro AP 0.4665, AUC 0.5721.
- Multi-Head: macro AP 0.4498, AUC 0.5498.

Vs Multi-Head, los deltas de AP macro son robustos para CatBoost especialista (+0.0222), RF (+0.0201) y pooled CatBoost (+0.0167), con IC95% completamente positivos.

T1 y T2 también muestran ventajas robustas de especialistas tabulares frente a los heads actuales.

### Lectura

E005 fue correctamente marcado como inconcluso con un único holdout; E006 resuelve esa incertidumbre y cambia la recomendación arquitectónica. Multi-Head deja de ser el baseline líder.

Para detalle y caveats: [EV-011](../../Evidencias/EV-011_modelo_3_architecture_cv.md).
