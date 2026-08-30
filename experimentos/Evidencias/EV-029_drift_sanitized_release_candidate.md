# EV-029 — Drift-sanitized release candidate

**Estado:** artifact construido y congelado; **FROZEN_AWAITING_PROSPECTIVE_GATE**. No es launch-eligible todavía.

**Experimento:** [E029](../feature_validation/E029_drift_sanitized_release_candidate/)

## Pregunta

¿Puede congelarse un LeadQuality T2-only que conserve señal útil después de retirar los clocks/progreso y las familias no robustas identificadas por E021–E027?

## Resultado de implementación

Sí: E029 ya produjo artifacts reproducibles y versionados:

- preprocessor;
- Random Forest T2;
- calibrador Platt;
- feature schema;
- release manifest candidato con hashes.

El manifest registra:

- `artifact_status = FROZEN_AWAITING_PROSPECTIVE_GATE`;
- `launch_eligible = false`;
- 244 features encoded;
- 7,351 filas de fit;
- 1,716 de calibration;
- 666 en historical sanity score;
- hashes SHA256 de preprocessor, modelo, calibrador, schema y treatment policy.

## Política congelada

LeadQuality elimina:

- `score_weekday`, `score_hour`, `score_month`;
- `days_from_lead_creation`, `inquiry_number`, `days_since_first_inquiry`;
- `prior_searches`;
- toda Availability dentro de LeadQuality;
- broker prior.

T0/T1 quedan neutrales. Availability permanece fuera del modelo como `InventoryServiceable` auditable de E028.

La target usa el contrato canónico E028: eventos con timing ambiguo se excluyen, nunca se convierten a 0.

## Auditoría de labels

Con la target corregida:

- snapshots T2 elegibles: **9,067**;
- leads T2 únicos: **3,328**;
- primera T2 por lead: **3,328**;
- ambiguous rows all stages: **1,478 (7.50%)**;
- positive rate first-T2: **38.91%**.

La corrección de target importa porque esos ambiguos no pueden convertirse silenciosamente en negativos.

## Diagnóstico histórico post-selección

Calibration partition, primera T2 por lead:

- N: **666**;
- positive rate: **50.75%**;
- AUC: **0.543**;
- AP: **0.542**;
- AP/prevalencia: **1.069**;
- Lift@10: **1.147x**;
- Brier: **0.249**;
- max numeric PSI train→calibration: **0.074**.

Rolling post-selection:

- 5 folds;
- AUC medio: **0.534**;
- AUC mínimo: **0.502**;
- AP/prevalencia mínimo: **0.985**;
- Lift@10 mínimo: **0.802x**.

**Interpretación:** existe señal residual modesta en T2, pero no es estable de forma suficiente como para llamar al histórico una confirmación.

## Por qué el histórico NO abre E028

E021–E027 ya usaron este periodo para decidir qué features retirar. Por ello:

- rolling histórico = diagnóstico post-selección;
- calibration partition histórica = sanity check;
- **ningún resultado histórico de E029 puede abrir E028**;
- reutilizarlo como confirmación introduciría selection bias.

El gate real requiere una cohorte creada estrictamente después del freeze/data cutoff.

## Gate prospectivo

Unidad:

- primera T2 elegible por lead posterior al freeze.

Ventana:

- primeras 8 semanas completas post-freeze;
- si hay <500 leads maduros, extender por semanas completas;
- máximo 16 semanas;
- la extensión depende sólo de N, nunca de outcomes.

PASS sólo si:

- N >=500 leads maduros;
- AUC point >=0.55;
- lower 95% CI AUC >0.50;
- AP/prevalencia >=1.05;
- Lift@10 >=1.10;
- timestamp real de scheduled_visit >=99.5%;
- sin fallo de leakage/instrumentación.

Si después de 16 semanas hay <500 leads maduros:

`INCONCLUSIVE_INSUFFICIENT_SAMPLE`.

No se modifican thresholds después de mirar outcomes.

El evaluador ya está implementado en [evaluate_prospective_gate.py](../feature_validation/E029_drift_sanitized_release_candidate/evaluate_prospective_gate.py).

## Estado causal

Aunque E029 pase el gate prospectivo, aún se requiere:

1. A/A productivo de assignment/outcome instrumentation;
2. completar y congelar el release manifest E028;
3. verificar hashes/versiones de Treatment;
4. sólo entonces abrir randomización real E028.

## Qué falta realmente

**No falta otro experimento offline. Falta información futura genuina.**

El paquete candidato termina antes del freeze requerido; por diseño no puede contener una cohorte post-freeze independiente. Simularla o reutilizar un holdout ya inspeccionado debilitaría precisamente la protección contra drift que motivó E029.

## Archivos fuente

- [README](../feature_validation/E029_drift_sanitized_release_candidate/README.md)
- [Summary](../feature_validation/E029_drift_sanitized_release_candidate/results/summary.json)
- [Report](../feature_validation/E029_drift_sanitized_release_candidate/results/REPORT.md)
- [Manifest candidato](../feature_validation/E029_drift_sanitized_release_candidate/artifacts/release_manifest_candidate.json)
- [Gate prospectivo](../feature_validation/E029_drift_sanitized_release_candidate/prospective_gate.json)
- [Evaluator](../feature_validation/E029_drift_sanitized_release_candidate/evaluate_prospective_gate.py)

## Descubrimiento relacionado

[D078](../conocimiento_agregado/DESCUBRIMIENTOS.md#d078--)
