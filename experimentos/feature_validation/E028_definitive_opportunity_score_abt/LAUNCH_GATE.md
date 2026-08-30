# E028 — Launch gate definitivo

## Estado actual

**Protocol / target:** READY / PRE-REGISTERED.

**Release candidate E029:** BUILT + FROZEN.

**Traffic launch:** **BLOCKED_PENDING_PROSPECTIVE_GATE_AND_PRODUCTION_AA**.

El trabajo offline de selección ya terminó. No se abre tráfico real hasta obtener evidencia genuinamente posterior al freeze del artifact.

## Gates resueltos por E021–E027

| Gate | Estado | Decisión |
|---|---|---|
| Temporal drift | PASS como diagnóstico / riesgo confirmado | monitoring temporal y validación post-freeze obligatorios |
| Raw clocks/progress | BLOCK | no entran al release candidate |
| Availability raw age | BLOCK como señal comercial | freshness se usa como guardrail/serviceability |
| Outlier deletion | REJECTED | conservar outliers salvo regla independiente de calidad |
| Price-total redundancy | INCONCLUSIVE | mantener en v1; no retirar sólo por preferencia de ingeniería |
| prior_searches | BLOCK | retirar |
| broker prior | BLOCK | fuera del Treatment/routing |

Evidencia central: EV-021–EV-027.

## Gate de artifact — E029

**Estado: PASS para build/freeze.**

E029 ya persistió:

- preprocessor;
- RF T2;
- Platt calibrator;
- feature schema;
- SHA256 de artifacts;
- treatment policy hash;
- manifest candidato.

Stage policy congelada:

- T0: LeadQuality neutral;
- T1: LeadQuality neutral;
- T2: candidate score sólo si pasa prospective gate.

El histórico E029 es sanity-check, no confirmación.

## Gate prospectivo — PENDIENTE

El evaluator está implementado en:

`../E029_drift_sanitized_release_candidate/evaluate_prospective_gate.py`.

Población:

- primera T2 elegible por lead;
- lead creado estrictamente después del freeze/data cutoff;
- primeras 8 semanas completas;
- extender por semanas completas sólo si N<500;
- máximo 16 semanas;
- extensión depende sólo de N, nunca de outcomes.

PASS requiere simultáneamente:

1. N >=500 leads maduros;
2. AUC >=0.55;
3. lower IC95% AUC >0.50;
4. AP/prevalencia >=1.05;
5. Lift@10 >=1.10;
6. completitud real de scheduled_visit event timestamp >=99.5%;
7. sin failure de leakage/instrumentation.

Si después de 16 semanas N<500:

`INCONCLUSIVE_INSUFFICIENT_SAMPLE`.

No se modifican thresholds después de observar outcomes.

## Gate de target/instrumentación

### Retrospectivo

El A/A dry run del paquete candidato valida:

- assignment único por lead;
- ventana de 30 días;
- ambiguos no convertidos en negativos;
- una fila de outcome por lead;
- SRM sin evidencia de mismatch.

Pero sólo **95.19%** de los leads maduros tiene target retrospectivamente observable bajo event-time conocido. Esto no cumple el estándar productivo.

### Productivo — PENDIENTE

Antes del primer assignment real se exige:

- timestamp backend real de scheduled_visit;
- completitud >=99.5%;
- tabla assignment con unique key `experiment_id × lead_id`;
- assignment persistido antes de scoring/routing;
- sticky arm;
- cero cross-arm assignment;
- A/A productivo sin SRM no explicado;
- logging completo de score, policy version, model version, feature schema y fallback.

La falta de event timestamp es un blocker de instrumentación, nunca outcome=0.

## Gate de freeze final — PENDIENTE

Después de PASS prospectivo y A/A productivo:

1. completar `RELEASE_MANIFEST_TEMPLATE.json`;
2. copiar hashes definitivos del candidate aprobado;
3. guardar git SHA;
4. guardar protocol/target/treatment-policy hashes;
5. congelar model/calibrator/schema/policy;
6. no retrain ni modificar UI/routing durante E028.

Cualquier cambio material después del freeze requiere nueva versión del experimento.

## Gate estadístico del A/B

Diseño pre-registrado:

- randomización: lead_id;
- 50/50 sticky;
- estratos: sector × modalidad × user_type;
- primary: `lead_scheduled_visit_30d_from_assignment`;
- horizon: 30 días;
- estimand: ITT absolute risk difference;
- alpha: 0.05;
- power: 80%;
- MDE: +2.0 pp;
- planificación conservadora p≈0.50;
- **9,806 leads maduros por brazo / 19,612 total**.

El tamaño fue reconciliado con la aproximación estándar de dos proporciones para p0=0.50 vs p1=0.52.

## Regla de decisión

### SHIP

- delta ITT >= +2.0 pp;
- lower IC95% >0;
- hard guardrails pasan.

### NO-SHIP

- upper IC95% < +2.0 pp.

### INCONCLUSIVE

Cualquier otro resultado estadísticamente válido.

### INVALID / NEEDS_REPAIR

- SRM no explicado;
- cross-arm assignment;
- pérdida material/asimétrica del outcome;
- violación de protocolo/instrumentación.

Secondary metrics nunca rescatan un primary fallido o inconcluso.

## Qué falta

No falta otro análisis offline de este mismo histórico.

Faltan dos observaciones que sólo producción/tiempo puede generar:

1. **cohorte post-freeze para E029**;
2. **A/A productivo de instrumentación**.

Una vez ambos pasen, el sistema queda listo para iniciar E028.
