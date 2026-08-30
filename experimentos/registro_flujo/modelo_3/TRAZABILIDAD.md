# Trazabilidad — pregunta → experimento → evidencia → decisión

| Pregunta | Experimento / análisis | Evidencia | Descubrimientos principales | Resultado |
|---|---|---|---|---|
| ¿Conviene modelar etapas por separado? | E003 Multi-Head | EV-003 | D003 | Multi-Head gana al pooled NN original |
| ¿Qué explica el valor de T2? | Interpretabilidad T2 | EV-004 | D004, D013–D017 | interaction_history / trayectoria domina |
| ¿Multi-Head gana a challengers fuertes? | E005 benchmark | EV-009 | D018–D022 | single holdout no resuelve macro AP |
| ¿Se replica con varias cohortes temporales? | E006 rolling CV | EV-011 | D019–D022, D034 | sí; modelos tabulares superan Multi-Head |
| ¿Trajectory aporta información incremental? | E007 trajectory CV | EV-012 | D035–D037 | sí en pooled CatBoost/Multi-Head T2; no universal |
| ¿Qué arquitectura queda? | consolidación | DECISION_ARQUITECTURA.md | D020, D034–D037 | pooled CatBoost + stage + trajectory |

## Cadena de evidencia final

```text
Pregunta dinámica
   ↓
E003 Multi-Head
   ↓
EV-003 / D003
   ↓
Interpretabilidad T2
   ↓
EV-004 / D004,D013-D017
   ↓
E005 challengers fuertes
   ↓
EV-009 / D018-D022
   ↓
E006 rolling temporal CV
   ↓
EV-011 / D019-D022,D034
   ↓
E007 trajectory CV
   ↓
EV-012 / D035-D037
   ↓
DECISION_ARQUITECTURA.md
```

## Artifacts fuente

### E003
- `experimentos/modelo_3/results/`
- `experimentos/Evidencias/harness_records/E003_modelo_3_multihead/`

### Interpretabilidad T2
- `experimentos/modelo_3/interpretabilidad_t2/results/`

### E005
- `experimentos/modelo_3/benchmark_specialists/results/`
- `experimentos/Evidencias/harness_records/E005_multihead_vs_specialists/`

### E006
- `experimentos/modelo_3/architecture_cv/results/`
- `experimentos/Evidencias/harness_records/E006_architecture_rolling_cv/`

### E007
- `experimentos/modelo_3/trajectory_cv/results/`
- `experimentos/Evidencias/harness_records/E007_trajectory_progression_cv/`

## Pull requests

- PR #3 — E003 Multi-Head.
- PR #5 — T2 interpretability.
- PR #8 — specialist benchmark.
- PR #10 — rolling CV + trajectory.

Todos fueron mergeados.
