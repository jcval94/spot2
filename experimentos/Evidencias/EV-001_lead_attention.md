# EV-001 — Lead attention / re-scoring T0→T1

**Estado de evidencia:** empírica, temporal, sobre target proxy `scheduled_visit`.

**Experimento:** [lead_attention](../lead_attention/)

## Evidencia fuente

- [Findings](../lead_attention/findings.md)
- [Código](../lead_attention/run_experiment.py)
- Resultados regenerables en `../lead_attention/results/`.

## Resultado central

T0: AUC 0.492, AP 0.527, Lift@10% 0.87x.

T1 primera inquiry: AUC 0.632, AP 0.621, Lift@10% 1.22x.

Esto respalda re-scoring dinámico después de observar interacción.

## Caveats

- Datos sintéticos.
- `scheduled_visit` es proxy de avance, no venta.
- La comparación no atribuye causalidad a una feature concreta.

**Descubrimiento:** [D001](../conocimiento_agregado/DESCUBRIMIENTOS.md#d001--el-modelo-debe-ser-dinámico).
