# EV-030 — ABT definitiva de Lead Opportunity

**Estado:** PASS reproducible.

**Experimento:** [E030](../feature_validation/E030_definitive_abt/)

## Resultado

La ABT canónica quedó construida y validada en CI.

- audit rows: **20,738**;
- audit unique leads: **5,000**;
- model-ready rows: **18,237**;
- model-ready unique leads: **4,648**;
- ambiguous rows preservadas: **1,478**;
- right-censored preservadas: **1,023**;
- model features: **68**;
- policy guardrails: **10**;
- audit-only: **7**;
- forbidden columns materializadas: **0**.

Split por lead:

- train: **3,253 leads**;
- validation: **697**;
- test: **698**.

La validación comprobó prediction key único, target binaria sólo en model-ready, preservación de ambiguous/censoring, aislamiento por lead, orden temporal train→val→test, stage semantics, stage policy, weights y coincidencia exacta del feature set con E029.

## Grain

Una fila = `lead_id × stage × score_time`.

T0 es alta; T1 primera inquiry; T2 segunda o posterior inquiry pre-visita.

## Target

Se usa únicamente el contrato E028. Ambiguous y right-censored nunca se convierten a 0.

## Gobernanza

- model_feature = E029 drift-sanitized;
- policy_guardrail = Availability/freshness;
- audit_only = clocks/progreso + prior_searches;
- forbidden = no materializado.

## Evidencia fuente

- [ABT contract](../feature_validation/E030_definitive_abt/ABT_CONTRACT.md)
- [ABT summary](../feature_validation/E030_definitive_abt/results/abt_summary.json)
- [Validation](../feature_validation/E030_definitive_abt/results/validation.json)
- [Schema](../feature_validation/E030_definitive_abt/results/abt_schema.json)
- [Column roles](../feature_validation/E030_definitive_abt/results/column_roles.csv)

## Conocimiento acumulado

Descubrimientos promovidos en [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
