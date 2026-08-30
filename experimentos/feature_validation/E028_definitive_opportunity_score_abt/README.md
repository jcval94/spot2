# E028 — A/B test definitivo del Lead Opportunity Score

## Pregunta de decisión

**¿Cambiar la priorización de Growth desde el proceso actual hacia un sistema dinámico de Lead Opportunity + disponibilidad/fallback incrementa la proporción de leads que agenda al menos una visita dentro de 30 días?**

Ésta es la prueba causal final del sistema, no otro benchmark de modelos.

## Control vs tratamiento

### A — Control

Proceso actual de Growth: priorización/routing existente e inventario actual, sin el score experimental.

### B — Tratamiento

Sistema dinámico completo:

1. T0 al alta;
2. T1 tras primera inquiry;
3. T2 en interacciones posteriores;
4. ranking operativo por Opportunity Score;
5. disponibilidad/frescura incorporada;
6. fallback compatible cuando el spot solicitado no puede atenderse.

El tratamiento es deliberadamente **sistémico**. Los experimentos offline anteriores sirven para escoger/depurar componentes; E028 responde si el producto completo genera impacto.

## Estado actual

- Protocolo causal: **PRE-REGISTERED / READY**.
- Target: **FROZEN**.
- Evidencia E021–E027: **COMPLETE**.
- Release candidate predictivo: **BUILT / FROZEN en E029; no launch-eligible hasta prospective gate PASS + A/A productivo**.

Ver [OFFLINE_DECISIONS.md](OFFLINE_DECISIONS.md).

## Target primaria

`lead_scheduled_visit_30d_from_assignment`.

Una sola observación por lead randomizado. Es 1 si hay cualquier `scheduled_visit` durante los 30 días posteriores a `assignment_at`.

La definición formal está en [TARGET.md](TARGET.md), [target_contract.json](target_contract.json) y su implementación canónica en [target_contract.py](target_contract.py).

## Randomización

- unidad: `lead_id`;
- 50/50 sticky;
- randomización antes de cualquier decisión experimental;
- estratos: sector × modalidad × user_type;
- análisis primary: intention-to-treat.

Randomizar por inquiry sería incorrecto: un mismo lead podría recibir simultáneamente control y tratamiento, y además los T2 del mismo lead no son independientes.

## Power y efecto mínimo

Debido al drift observado no se toma 34.3% como una verdad estable de baseline.

Se pre-registra un **MDE práctico de +2 puntos porcentuales absolutos**. Para no depender de una baseline optimista se dimensiona conservadoramente cerca del peor caso binomial p≈0.50:

- 9,806 leads maduros por brazo;
- 19,612 leads maduros total;
- alpha 0.05;
- power 80%.

No se debe mirar el efecto y después cambiar el MDE.

## Regla de decisión

**SHIP** sólo si:

1. estimación ITT >= +2.0 pp;
2. límite inferior IC95% > 0;
3. guardrails duros aprobados.

**NO-SHIP** si el límite superior IC95% es < +2.0 pp: el test ya descartó el efecto mínimo práctico.

Cualquier otro caso es **INCONCLUSIVE**.

## Drift temporal

El experimento no intenta “arreglar” drift ocultándolo.

- monitoreo semanal ciego de covariables;
- outcome agregado maduro sólo para QA, sin comparar brazos durante la corrida;
- análisis secundario por assignment week;
- sensitivity model ajustado por assignment week + estratos;
- muestra fija y 30 días de maduración;
- sin optional stopping.

## Por qué éste es el A/B definitivo

Los A/B anteriores de perfiles responden preguntas de representación. E028 mide la decisión que realmente importa: si **usar** el sistema cambia el resultado comercial del lead.

Un modelo puede mejorar AP y no mejorar visitas si el equipo no actúa sobre el score, si el inventario falla o si el routing crea fricción. El A/B sistémico captura todas esas rutas.

## Archivos

- [TARGET.md](TARGET.md) — definición canónica del label offline y outcome online.
- [target_contract.json](target_contract.json) — contrato machine-readable de grain, ventana, estados y censura.
- [OFFLINE_DECISIONS.md](OFFLINE_DECISIONS.md) — decisiones E021–E027 y feature/stage gates.
- [TREATMENT_POLICY.md](TREATMENT_POLICY.md) — fórmula del score, serviceability y fallback congelados.
- [LAUNCH_GATE.md](LAUNCH_GATE.md) — condiciones E021–E027 que deben cumplirse antes de randomizar.
- [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) — estimand, ITT, SRM, intervalos, drift y decisión.
- [ab_test_protocol.json](ab_test_protocol.json) — protocolo machine-readable.
- [experiment_spec.json](experiment_spec.json) — pre-registro causal; no usa el schema del harness predictivo.
- [EVIDENCIA.md](EVIDENCIA.md)


## Release candidate asociado

El artifact de LeadQuality está en [E029](../E029_drift_sanitized_release_candidate/).

- T0: neutral.
- T1: neutral.
- T2: score congelado sólo después de prospective gate PASS.
- El histórico E029 es sanity-check post-selección; no abre tráfico.
