# EV-028 — Target definitiva + A/B test definitivo

**Estado:** protocolo causal pre-registrado y target congelada; E029 ya produjo un release candidate drift-sanitized congelado, pero **launch sigue bloqueado** hasta superar el gate prospectivo post-freeze y un A/A productivo de instrumentación.

**Experimento:** [E028](../feature_validation/E028_definitive_opportunity_score_abt/)

## Decisión

La prueba causal final para Spot2 debe responder una sola pregunta:

> ¿Asignar un lead al sistema dinámico de Opportunity + serviceability/fallback aumenta la probabilidad de agendar al menos una visita dentro de 30 días frente al proceso actual de Growth?

No se usa AUC/AP como criterio de éxito del A/B. Esas métricas sirven para construir el tratamiento; el RCT mide impacto real de usarlo.

## Target offline canónica

Para scoring en tiempo `t`:

`target_scheduled_visit_30d(l,t)=1`

si existe al menos un evento único `broker_response == scheduled_visit` con:

`t < response_event_at <= t + 30 días`.

Condiciones:

- ninguna visita ya observada antes de `t`;
- 30 días completos de maduración;
- features disponibles en o antes de `t`;
- snapshots inmaduros se censuran, no se etiquetan 0;
- múltiples snapshots del mismo lead son válidos offline, pero splits/bootstrap respetan `lead_id`.

## Primary outcome online

Para cada lead randomizado una sola vez:

`lead_scheduled_visit_30d_from_assignment = 1`

si existe cualquier evento backend **único** de scheduled_visit en:

`(assignment_at, assignment_at + 30 días]`.

- grain: una fila por `lead_id`;
- múltiples visitas cuentan una vez;
- eventos técnicos duplicados se deduplican antes de agregar;
- `assignment_at` se persiste en UTC **antes** de score, queue ordering o routing experimental;
- primera asignación gana y es inmutable;
- denominador ITT = todos los leads elegibles randomizados, incluso fallos de scoring/fallback.

## Calidad del timestamp del outcome

En candidate data, `response_event_at` se reconstruye desde `inquiry_at + broker_response_hours`. El EDA observó **14.97% de missing en broker_response_hours dentro de scheduled_visit**.

Esto introduce incertidumbre de timing en el histórico. La target definitiva corrige la semántica:

- known event inside window → 1;
- no event and full observability → 0;
- scheduled_visit de timestamp desconocido que podría caer en la ventana → **AMBIGUOUS**, no 0;
- producción → timestamp backend real obligatorio.

Por eso E021–E027 siguen siendo útiles para decisiones de feature/drift, pero sus métricas absolutas heredan label timing noise del target histórico anterior y no deben usarse como calibración final del A/B.

## Por qué scheduled_visit y 30 días

Es el mejor outcome observable del paquete candidato que representa progreso comercial material. `accepted` es demasiado débil; cierre/revenue no tiene todavía ground truth con cobertura/maduración defendible.

El horizonte fijo de 30 días es especialmente importante porque E021 confirmó drift fuerte de cohortes. Evita que una cohorte "gane" simplemente porque tuvo más tiempo observable.

Cuando exista producción confiable:

- `close_90d` / `revenue_90d` deben añadirse como north-star secundario;
- no deben sustituir retrospectivamente la primary target iniciada.

## Evidencia offline que cambió el Treatment

La suite E021–E027 terminó reproduciblemente en GitHub Actions:
https://github.com/jcval94/spot2/actions/runs/33281869820

La conclusión crítica es E022 / EV-022:

- RF completo macro AUC 0.556, AP 0.517;
- sin clocks/progreso AUC 0.512, AP 0.485;
- diagnóstico time-proxy-only AUC **0.596**, AP **0.549**;
- en T1, quitar clocks lleva AUC **0.588 → 0.504** y AP **0.563 → 0.510**.

Por tanto, el RF T1 de E005 **no puede lanzarse tal cual**. Su ventaja offline estaba materialmente asociada a una estructura temporal que E021 demuestra inestable.

Otras decisiones:

- raw Availability snapshot age fuera como señal comercial; freshness sí como guardrail (EV-023);
- no borrar outliers automáticamente (EV-024);
- price totals: decisión formal aún inconclusa bajo el margen pre-registrado (EV-025);
- retirar `prior_searches` (EV-026);
- broker prior fuera del Treatment (EV-027).

## Diseño A/B definitivo

### Randomización

- unidad: `lead_id`;
- 50/50 sticky;
- antes de cualquier exposición;
- estratos: `search_sector × search_modality × user_type`;
- preferencia de implementación: bloques permutados dentro de estrato;
- análisis primario: intention-to-treat.

### A — Control

Proceso actual de Growth, sin Opportunity Score ni fallback experimental.

### B — Treatment

Una política **congelada** de:

- LeadQuality drift-sanitized sólo en stages que pasen el gate futuro;
- inventory serviceability auditable;
- freshness explícita;
- fallback gobernado cuando el Spot solicitado no sea servible;
- misma asignación del lead durante T0/T1/T2.

Con la evidencia actual:

- T0: LeadQuality neutral salvo validación adicional;
- T1: **LeadQuality neutral**; el modelo actual está bloqueado;
- T2: puede ordenar sólo si el candidato sanitizado confirma su señal residual en una cohorte futura.

## Power

Pre-registro:

- alpha: 0.05;
- power: 80%;
- MDE práctico: **+2.0 pp absolutos**;
- planificación conservadora alrededor de p=0.50 por el drift;
- **9,806 leads maduros por brazo**;
- **19,612 total**.

Si el tráfico real no soporta ese tamaño, el MDE se modifica **antes** de iniciar el experimento, nunca después de observar efectos.

## Regla de decisión

**SHIP**

- delta ITT >= +2.0 pp;
- límite inferior IC95% >0;
- guardrails duros pasan.

**NO-SHIP**

- límite superior IC95% < +2.0 pp.

**INCONCLUSIVE**

- cualquier otro resultado estadísticamente válido.

**INVALID / NEEDS_REPAIR**

- SRM no explicado;
- cross-arm assignment;
- pérdida material/asimétrica del outcome;
- violación grave de instrumentación/protocolo.

Secondary metrics no pueden convertir un primary fallido/inconcluso en SHIP.

## Drift durante el A/B

La randomización concurrente protege el contraste de drift común, pero no su transportabilidad.

Se pre-registra:

- monitoring semanal ciego de covariables;
- resultado por assignment week como heterogeneidad secundaria;
- ajuste de sensibilidad por assignment week + estratos;
- 30 días completos de maduración;
- fixed sample;
- no optional stopping ni peeking del efecto.

## A/A y release freeze

Antes de launch:

1. `validate_protocol.py` prueba target, denominador, asignación y SRM sobre candidate data;
2. un A/A equivalente debe validar instrumentación productiva;
3. `RELEASE_MANIFEST_TEMPLATE.json` se completa con SHA, model/calibrator versions y hashes;
4. modelo, schema, target, serviceability y UI/routing quedan congelados.

El A/A no es evidencia de tratamiento; sólo valida que el experimento pueda medirlo limpiamente.

## A/A retrospectivo del protocolo

El dry run de `validate_protocol.py` sobre candidate data produjo:

- leads maduros candidatos: **4,841**;
- target observable retrospectivamente: **4,608 (95.19%)**;
- labels `AMBIGUOUS_UNKNOWN_EVENT_TIME`: **233**;
- scheduled_visit rows sin event time: **14.97%**;
- primary rate entre casos observables: **38.98%**;
- rango extremo por incertidumbre de timing: **37.10%–41.91%**;
- pseudo-asignación Control/Treatment: **2,430 / 2,411**;
- SRM p-value: **0.785**;
- pseudo-delta A/A observable: **+0.97 pp** — no causal;
- cobertura del tamaño requerido para MDE +2pp: **24.68%**.

**Lectura:** el plumbing de assignment pasa el control SRM y la target no convierte los ambiguos en negativos. El histórico, sin embargo, no alcanza el gate productivo de >=99.5% de timestamp del outcome y tampoco tiene tamaño para ejecutar el RCT definitivo. Eso es esperado: E028 es un diseño prospectivo.

Resultados: [dry_run_results](../feature_validation/E028_definitive_opportunity_score_abt/dry_run_results/).

## Release candidate E029

E029 ya resolvió el blocker de construcción del Treatment:

- artifact status: `FROZEN_AWAITING_PROSPECTIVE_GATE`;
- T0/T1: LeadQuality neutral;
- T2: RF drift-sanitized congelado;
- AUC histórica de sanity-check: **0.543**;
- AP/prevalencia: **1.069**;
- Lift@10: **1.147x**;
- PSI numérico máximo train→calibration: **0.074**;
- hashes de preprocessor, model, calibrator, schema y treatment policy persistidos.

Pero este histórico **no es confirmatorio**, porque E021–E027 participaron en la selección de la política. El único gate válido es la primera cohorte genuinamente post-freeze definida en `E029/prospective_gate.json`.

PASS del candidato exige:

- >=500 leads maduros first-T2;
- AUC >=0.55;
- lower IC95% AUC >0.50;
- AP/prevalencia >=1.05;
- Lift@10 >=1.10;
- completitud real del timestamp scheduled_visit >=99.5%;
- cero fallos de leakage/instrumentación.

Después de PASS todavía se requiere A/A productivo y freeze final del manifest E028.

Evidencia: [EV-029](EV-029_drift_sanitized_release_candidate.md).

## Estado final

**La target y el protocolo causal están listos; el release candidate existe y está congelado. Lo único que impide abrir tráfico es evidencia prospectiva post-freeze + instrumentación productiva A/A.**

No existe más trabajo offline honesto que pueda sustituir ese pendiente: reutilizar el histórico para “confirmar” E029 introduciría selection bias.

## Archivos fuente

- [TARGET.md](../feature_validation/E028_definitive_opportunity_score_abt/TARGET.md)
- [TREATMENT_POLICY.md](../feature_validation/E028_definitive_opportunity_score_abt/TREATMENT_POLICY.md)
- [OFFLINE_DECISIONS.md](../feature_validation/E028_definitive_opportunity_score_abt/OFFLINE_DECISIONS.md)
- [ANALYSIS_PLAN.md](../feature_validation/E028_definitive_opportunity_score_abt/ANALYSIS_PLAN.md)
- [LAUNCH_GATE.md](../feature_validation/E028_definitive_opportunity_score_abt/LAUNCH_GATE.md)
- [Protocol JSON](../feature_validation/E028_definitive_opportunity_score_abt/ab_test_protocol.json)
- [Release manifest](../feature_validation/E028_definitive_opportunity_score_abt/RELEASE_MANIFEST_TEMPLATE.json)
- [A/A validator](../feature_validation/E028_definitive_opportunity_score_abt/validate_protocol.py)
- [Spec](../feature_validation/E028_definitive_opportunity_score_abt/experiment_spec.json)


## Descubrimientos relacionados

- [D075](../conocimiento_agregado/DESCUBRIMIENTOS.md#d075--)
- [D076](../conocimiento_agregado/DESCUBRIMIENTOS.md#d076--)
- [D077](../conocimiento_agregado/DESCUBRIMIENTOS.md#d077--)
- [D078](../conocimiento_agregado/DESCUBRIMIENTOS.md#d078--)
