# EV-038 — Stage-aware Feature Policy v2

**Estado:** DECISION-FREEZE.

[E038](../feature_validation/E038_stage_aware_feature_policy/)

E031–E037 agotaron una batería amplia de Feature Engineering sobre los campos actuales:

- logs/scale/specificity;
- semantic Search Need;
- Dynamic Need;
- soft cluster distances;
- Physical/Location;
- semantic interactions;
- missingness/frequency;
- robust bins;
- inventory-relative;
- preferred-geo distance;
- temporally smoothed target encodings.

## Decisión por etapa

### T0

**LeadQuality = NEUTRAL_EVIDENCE_BACKED.**

Search Need/specificity permanecen como representación explicativa/operativa, pero no existe evidencia para rankear leads por propensión a visita.

### T1

**LeadQuality = NEUTRAL_EVIDENCE_BACKED.**

Dynamic Need, Need transition, PH/LOC y Lead×Spot compatibility permanecen como representación para matching/routing experimental. No se promueven a LeadQuality.

### T2

**LeadQuality = E029 FROZEN CANDIDATE PENDING PROSPECTIVE GATE.**

## Regla de reapertura

T0/T1 se reabren con nueva información, no con más combinaciones del mismo holdout:

- raw inquiry text;
- geo preferida canónica;
- effective-dated market/inventory context;
- true close/lease outcome;
- nueva cohorte temporal independiente.

Fuente: [FEATURE_POLICY_V2.json](../feature_validation/E038_stage_aware_feature_policy/FEATURE_POLICY_V2.json).


## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
