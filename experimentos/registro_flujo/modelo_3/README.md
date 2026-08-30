# FL-001 — Modelo 3 / Dynamic Lead Quality

**Estado:** **CLOSED / DECISION-READY**

**Pregunta que cerramos:**  
¿Cuál es la arquitectura más defendible para re-scorear dinámicamente Lead Quality a medida que un lead avanza de T0 a T1/T2, y qué información explica el valor adicional de las etapas avanzadas?

## Respuesta final

La investigación comenzó defendiendo una arquitectura **shared backbone + stage-specific heads**. La evidencia posterior obligó a cambiar esa recomendación.

La decisión actual es:

```text
point-in-time scoring snapshot
          │
          ▼
 pooled CatBoost + stage
          │
 + trajectory/progression
          ▼
 dynamic Lead Quality score
```

Los especialistas CatBoost / Random Forest se conservan como challengers por etapa, especialmente T1/T2.

No se recomienda todavía un router de modelos distinto por etapa: la familia seleccionada cambia entre folds temporales.

## Por qué se considera cerrado

La línea ya pasó por:

- baseline multi-head;
- interpretación T2;
- challengers tabulares fuertes;
- comparación equivalente;
- rolling temporal cross-validation;
- bootstrap por lead;
- feature engineering de trajectory bajo los mismos folds;
- revisión de leakage point-in-time;
- actualización de descubrimientos y evidencia;
- decisión arquitectónica explícita.

La conclusión no depende de un único holdout.

## Qué **no** significa “cerrado”

No significa que el score esté listo para producción real.

Quedan como fase posterior:

- ablation del bloque trajectory;
- calibración/threshold según capacidad operativa;
- política de routing;
- monitoreo de drift;
- validación contra outcome comercial real.

Esos pasos refinan o productizan la solución; **no reabren la pregunta arquitectónica básica** salvo que nueva evidencia contradiga E006/E007.

## Navegación

- [CRONOLOGIA.md](CRONOLOGIA.md) — secuencia completa E003→E007.
- [DECISIONES.md](DECISIONES.md) — qué decisiones cambiaron y por qué.
- [TRAZABILIDAD.md](TRAZABILIDAD.md) — pregunta → experimento → evidencia → descubrimiento.
- [INCIDENCIAS_Y_CORRECCIONES.md](INCIDENCIAS_Y_CORRECCIONES.md) — errores, leakage/governance y fixes.
- [CIERRE.md](CIERRE.md) — checklist formal de cierre.

## Fuentes canónicas

- [Decisión arquitectónica](../../modelo_3/DECISION_ARQUITECTURA.md)
- [EV-003 Multi-Head](../../Evidencias/EV-003_modelo_3_multihead.md)
- [EV-004 Interpretabilidad T2](../../Evidencias/EV-004_modelo_3_t2_interpretabilidad.md)
- [EV-009 Benchmark especialistas](../../Evidencias/EV-009_modelo_3_benchmark_specialists.md)
- [EV-011 Rolling CV](../../Evidencias/EV-011_modelo_3_architecture_cv.md)
- [EV-012 Trajectory CV](../../Evidencias/EV-012_modelo_3_trajectory_cv.md)
- [Descubrimientos acumulados](../../conocimiento_agregado/DESCUBRIMIENTOS.md)
