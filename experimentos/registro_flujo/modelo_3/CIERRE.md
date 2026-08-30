# Cierre formal — Modelo 3

## Veredicto

**CLOSED / DECISION-READY**

La pregunta arquitectónica de esta línea puede cerrarse.

## Checklist

- [x] Problema de negocio/modelado definido.
- [x] T0/T1/T2 y scoring time definidos.
- [x] Target móvil definido.
- [x] Censoring definido.
- [x] Leakage review point-in-time.
- [x] Baseline Multi-Head implementado.
- [x] Challenger pooled implementado.
- [x] Especialistas tabulares fuertes implementados.
- [x] Interpretabilidad T2.
- [x] Robustez por lead.
- [x] Comparación equivalente E005.
- [x] Rolling temporal CV E006.
- [x] OOF predictions.
- [x] Bootstrap por lead.
- [x] Feature engineering trajectory E007.
- [x] Resultados negativos preservados.
- [x] Evidencia central EV-011/EV-012.
- [x] Harness records persistidos.
- [x] Descubrimientos actualizados.
- [x] Decisión arquitectónica explícita.
- [x] GitHub Actions verde en `main`.

## Decisión vigente

**Baseline recomendado:** pooled CatBoost + stage + trajectory/progression.

**Challengers:** specialist CatBoost y Random Forest.

**No recomendado todavía:** router de familia por etapa.

## Qué quedó abierto, pero no bloquea el cierre

### 1. Ablation de trajectory

Útil para reducir el feature set y explicar qué subfamilia aporta:

- timing/velocity;
- unresolved response state;
- revisitas;
- cambios de restricciones;
- intención.

Esto es optimización del baseline, no una pregunta pendiente sobre Multi-Head vs tabular.

### 2. Threshold/routing policy

Debe ajustarse a capacidad real de brokers/operación.

No cambia la arquitectura del estimador.

### 3. Outcome comercial

`scheduled_visit` es proxy.

Cuando exista un outcome mejor, debe abrirse una **nueva línea o nueva generación del experimento**, porque cambia el target.

### 4. Producción

Faltan monitoreo, drift, retraining, latencia y serving.

Son MLOps/productización.

## Regla de reapertura

Reabrir FL-001 sólo si nueva evidencia contradice la decisión arquitectónica.

Si el trabajo es simplemente optimizar, calibrar o desplegar el baseline elegido, crear una nueva fase/flujo derivado en vez de reescribir esta historia.
