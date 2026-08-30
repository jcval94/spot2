# Decisión arquitectónica actual — Modelo 3

## Resumen

Después de E003→E007, **Multi-Head deja de ser la arquitectura recomendada por defecto**.

La opción más defendible hoy por balance entre desempeño, estabilidad y complejidad es:

```text
point-in-time snapshot
        │
        ▼
pooled CatBoost + stage
        │
        + trajectory/progression features
        ▼
dynamic Lead Quality score
```

Los especialistas por etapa se mantienen como challengers:

- T1: specialist CatBoost / Random Forest.
- T2: specialist CatBoost / Random Forest.

No se recomienda todavía un router de modelos por etapa porque la familia elegida con validation cambia entre folds.

## Evidencia que cambia la decisión

### E003 — Multi-Head vs pooled neural

Multi-Head superó al pooled neural original y justificó investigar heads por etapa.

### E005 — Challengers tabulares fuertes

El single holdout sugirió que CatBoost/RF podían superar al Multi-Head, pero macro AP todavía era incierto.

### E006 — Rolling temporal CV

La incertidumbre se resuelve:

- specialist CatBoost vs Multi-Head: macro ΔAP +0.0222, IC95% [+0.0068, +0.0361].
- specialist RF vs Multi-Head: macro ΔAP +0.0201, IC95% [+0.0078, +0.0321].
- pooled CatBoost + stage vs Multi-Head: macro ΔAP +0.0167, IC95% [+0.0016, +0.0315].

T1 y T2 también favorecen robustamente especialistas tabulares frente a los heads actuales.

### E007 — Trajectory features

Sobre los mismos folds:

- pooled CatBoost T2: ΔAP +0.0161, IC95% [+0.0003, +0.0322].
- Multi-Head T2: ΔAP +0.0155, IC95% [+0.0013, +0.0303].
- RF T2: ΔAP -0.0095, IC95% [-0.0191, -0.0002].

Por tanto, trajectory es señal real pero arquitectura-dependiente.

## Recomendación

### Baseline operativo

**pooled CatBoost + stage + trajectory features**

Motivos:

1. un único modelo;
2. supera al Multi-Head en CV temporal;
3. trajectory mejora T2;
4. evita un router inestable;
5. es más fácil de calibrar, desplegar, monitorear y explicar que varios heads/modelos.

### Challengers

Mantener:

- specialist CatBoost por etapa;
- specialist Random Forest, especialmente como benchmark T1/T2.

No declarar CatBoost especialista como ganador universal sobre RF por AP: sus diferencias directas son pequeñas y no robustas en AP.

## Siguiente experimento recomendado

Ablation de trajectory por subfamilias sobre pooled CatBoost:

1. **timing/velocity**;
2. **response-state / unresolved**;
3. **spot revisit/diversity**;
4. **constraint changes**;
5. **asked_visit/channel progression**.

Usar los mismos folds E006/E007 y comparar cada bloque contra el baseline congelado.

Después de identificar el mínimo conjunto útil, pasar a:

- calibración final por etapa;
- Lift/Recall bajo capacidad operativa;
- threshold/routing policy;
- validación con outcome comercial cuando exista.

## Evidencia

- [EV-003](../Evidencias/EV-003_modelo_3_multihead.md)
- [EV-009](../Evidencias/EV-009_modelo_3_benchmark_specialists.md)
- [EV-011](../Evidencias/EV-011_modelo_3_architecture_cv.md)
- [EV-012](../Evidencias/EV-012_modelo_3_trajectory_cv.md)
- [Descubrimientos acumulados](../conocimiento_agregado/DESCUBRIMIENTOS.md)
