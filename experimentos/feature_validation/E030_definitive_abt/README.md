# E030 — ABT definitiva de Lead Opportunity

## Objetivo

Materializar una única Analytical Base Table reproducible para el problema dinámico T0/T1/T2, usando:

- snapshots point-in-time;
- target canónica E028;
- política de features drift-sanitized E029;
- split temporal por lead;
- roles de columna explícitos para impedir reintroducir leakage/drift.

## Grain

Una fila representa una **oportunidad de scoring**:

`lead_id × stage × score_time × inquiry_id/spot_id context`.

Stages:

- T0: `score_time = leads.created_at`;
- T1: primera inquiry;
- T2: segunda y posteriores inquiries mientras no exista visita conocida antes del score.

Un lead puede tener varios T2 porque el sistema es de re-scoring.

## Dos tablas

### abt_all_snapshots.csv.gz

Auditoría completa. Conserva:

- POSITIVE;
- NEGATIVE;
- AMBIGUOUS_UNKNOWN_EVENT_TIME;
- RIGHT_CENSORED;
- INELIGIBLE_PRIOR_SCHEDULED_VISIT cuando aplique.

Nunca se usa directamente para entrenamiento binario.

### abt_model_ready.csv.gz

Sólo rows con target canónica observable:

- POSITIVE;
- NEGATIVE.

Los censurados y ambiguos se excluyen, nunca se convierten en 0.

## Roles

- `model_feature`: política drift-sanitized E029.
- `policy_guardrail`: Availability/freshness y serviceability context; no entra en LeadQuality.
- `audit_only`: clocks/progreso, prior_searches, IDs, timestamps, split, sample weight y metadata.
- `target`: target/status.
- `forbidden`: no se materializa.

## Release policy

La ABT soporta investigación T0/T1/T2, pero el release actual E029 es:

- T0 neutral;
- T1 neutral;
- T2 candidate pending prospective gate.

## Outputs

- `results/abt_all_snapshots.csv.gz`
- `results/abt_model_ready.csv.gz`
- `results/abt_schema.json`
- `results/abt_summary.json`
- `results/column_roles.csv`
- `results/stage_target_summary.csv`
- `results/split_summary.csv`
- `results/status_summary.csv`

## Ejecución

```bash
python experimentos/feature_validation/E030_definitive_abt/build_abt.py
python experimentos/feature_validation/E030_definitive_abt/validate_abt.py
```


## CI

La ABT se reconstruye y valida en `.github/workflows/e030-definitive-abt.yml`. Un CSV manual no se considera evidencia canónica.
