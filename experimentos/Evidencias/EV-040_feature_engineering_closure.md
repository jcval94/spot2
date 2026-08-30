# EV-040 — Cierre de Feature Engineering T0/T1

**Estado:** CLOSED / DECISION-READY.

**Artifact:** [E040](../feature_validation/E040_t0_t1_feature_engineering_closure/)

## Pregunta de cierre

Después de E020–E039, ¿queda trabajo offline obligatorio para considerar cerrada la investigación de Feature Engineering de T0/T1 con el dataset actual?

## Respuesta

**No.**

La evidencia ya cubre múltiples familias de FE, validación temporal, target corregida, ABT canónica y control de leakage. Seguir iterando sobre las mismas columnas/periodos tiene mayor riesgo de research-overfitting que valor esperado.

## Decisión final

### T0

- LeadQuality: `NEUTRAL_EVIDENCE_BACKED`.
- Search Need/specificity: representación explicativa/operativa.
- Sin score de propensión hasta nueva información.

### T1

- LeadQuality: `NEUTRAL_EVIDENCE_BACKED`.
- Dynamic Need / Need transition / PH / LOC / Lead×Spot fit: matching/routing experimental.
- No promover clusters a propensión sólo por interpretabilidad.

### T2

- E029 permanece candidato congelado sujeto a prospective gate.

## Qué sí se considera pendiente

Pendientes externos/de fase siguiente, no blockers del cierre:

- E029 prospective gate;
- E028 production A/A;
- raw inquiry text para E039;
- market/inventory effective-dated;
- true close/lease target;
- nueva cohorte independiente.

## Criterio de reapertura

Sólo con nueva información, nueva target, nueva temporalidad point-in-time o nueva cohorte.

No reabrir por tuning/K/cruces adicionales sobre el mismo histórico.

## Evidencia base

- EV-020–EV-030: EDA, drift, target y ABT.
- EV-031–EV-038: recuperación y policy.
- EV-039: LLM semantic inquiry features, bloqueado por data gap.

## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
