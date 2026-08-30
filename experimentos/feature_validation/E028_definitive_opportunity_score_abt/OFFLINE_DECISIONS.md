# E028 — Offline decisions before launch

Este documento convierte E021–E027 en decisiones de release. No reinterpreta métricas después de verlas: respeta los contratos y sus intervalos.

## Estado general

**A/B protocol:** READY / PRE-REGISTERED.

**Production treatment artifact:** NOT READY.

El blocker no es estadístico del A/B; es el release candidate predictivo. E022 demuestra que el modelo E005/T1 depende demasiado de clocks/progreso sujetos a drift.

## Gate decisions

| Experimento | Resultado | Decisión para release |
|---|---|---|
| E021 drift | SUPPORTED | Monitor temporal obligatorio; una sola cohorte no basta. |
| E022 temporal ablation | SUPPORTED / crítico | **BLOCK** modelo E005 tal cual; retirar/reformular clocks y validar de nuevo. |
| E023 availability | SUPPORTED | Raw snapshot age fuera como señal comercial; freshness explícita; >90d = unknown histórico. |
| E024 outliers | INCONCLUSIVE | Conservar outliers; Isolation Forest sólo QA/diagnóstico. |
| E025 redundancy | INCONCLUSIVE | Mantener price totals en v1 si se exige literalidad del gate; eliminar sólo tras confirmación adicional. |
| E026 prior history | NOT_SUPPORTED | Retirar `prior_searches`; `prior_inquiries` no tiene utilidad incremental demostrada. |
| E027 broker prior | INCONCLUSIVE | No incluir broker prior; no usarlo para routing. |

## Release candidate mínimo

La siguiente versión candidata debe construirse con estas restricciones:

### Bloqueados

- `score_weekday`
- `score_hour`
- `score_month`
- `days_from_lead_creation`
- `inquiry_number`
- `days_since_first_inquiry`
- `prior_searches`
- broker historical prior
- `availability_snapshot_age_days` como predictor crudo
- current-state Spot aggregates no reconstruidos point-in-time
- Market Context sin publication/effective time

Los clocks pueden seguir existiendo para **monitoring, SLA o reglas operativas**, pero no como input del release predictivo actual hasta superar una validación específica de estabilidad.

### Conservar por ahora

- lead intake no temporal;
- inquiry content/context point-in-time;
- Spot static;
- Lead↔Spot compatibility;
- interaction history no bloqueada por E022;
- availability state con freshness guardrail;
- outliers válidos;
- price totals en v1 si se mantiene la interpretación estricta de E025.

## Implicación por etapa

### T0

No existe evidencia limpia suficiente para una priorización ML agresiva. T0 debe usar una política neutral/control-compatible hasta que un modelo drift-sanitized demuestre lift futuro.

### T1

**No usar el RF E005 como release candidate.**

Al retirar clocks/progreso:

- AUC cae de 0.5877 a 0.5038;
- AP cae de 0.5628 a 0.5097.

T1 puede activar actualización de inventory/serviceability/fallback, pero el componente LeadQuality no debe reordenar leads usando el modelo actual.

### T2

Con el mismo stress, T2 conserva señal moderada:

- AUC 0.5736;
- AP 0.4912 sobre prevalencia 0.4318;
- Lift@10% 1.176x.

Eso lo convierte en el único stage con evidencia residual suficiente para una validación de release, **no en un modelo aprobado automáticamente**.

## Regla para abrir el A/B

Antes del primer assignment de E028:

1. entrenar el release candidate con el feature set sanitizado;
2. validarlo en una cohorte futura no usada en E021–E027;
3. exigir que T0/T1 sólo influyan en ranking si muestran discriminación/lift estable;
4. permitir T2 si mantiene señal y calibración aceptables;
5. guardar SHA/model artifact/calibrator/schema;
6. ejecutar A/A de assignment e instrumentación;
7. congelar política.

Si T0/T1 no superan el gate, la política definitiva no inventará score: permanecerán neutrales hasta que el lead alcance un stage validado.

## Por qué esto es preferible

El objetivo del A/B es medir si el **producto** funciona. Incluir un stage que sabemos que aprende principalmente calendario haría el tratamiento más complejo, menos interpretable y potencialmente menos transportable sin aportar evidencia sólida.

Un A/B definitivo no necesita usar todas las ideas offline; necesita usar sólo las que llegaron vivas al launch gate.
