# E029 — Drift-sanitized release candidate

## Objetivo

Construir la pieza que falta entre E028 y un A/B real: un LeadQuality **T2-only** que no dependa de los clocks/progreso que explicaron el drift.

## Política congelada

Se eliminan de LeadQuality:

- `score_weekday`, `score_hour`, `score_month`;
- `days_from_lead_creation`, `inquiry_number`, `days_since_first_inquiry`;
- `prior_searches`;
- toda Availability, incluida su edad;
- broker prior.

Availability queda en E028 como `InventoryServiceable`, no como señal probabilística del Lead.

Se conservan outliers y price totals porque E024/E025 no justificaron removerlos de forma robusta.

## Target

Usa la target canónica de E028:

`target_scheduled_visit_30d`

con estados ambiguos por event-time desconocido excluidos, nunca imputados a 0.

## Honestidad de validación

E021–E027 ya usaron el histórico para seleccionar la política. Por tanto:

- rolling CV sobre ese histórico = diagnóstico post-selección;
- NO se llamará “future confirmation”;
- el artifact se congela;
- la confirmación real ocurre en la primera cohorte **posterior al freeze** según `prospective_gate.json`.

## Stage policy

- T0: neutral.
- T1: neutral.
- T2: candidato congelado; sólo se activa en E028 si pasa el gate prospectivo.

## Salidas

- modelo/preprocessor/calibrador congelados;
- feature schema;
- manifest con hashes;
- auditoría de labels;
- rolling diagnostics históricos;
- protocolo prospectivo ejecutable.
