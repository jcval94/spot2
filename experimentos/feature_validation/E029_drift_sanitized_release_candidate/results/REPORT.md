# E029 — Drift-sanitized release candidate

## Estado

**FROZEN_AWAITING_PROSPECTIVE_GATE**

El artifact queda congelado, pero **launch_eligible=false** hasta observar una cohorte posterior al freeze.

## Target corregida

- T2 snapshots elegibles: 9,067
- leads T2 únicos: 3,328
- ambiguos detectados en todos los stages: 1,478 (7.50%)

Los ambiguos no se convierten en 0.

## Diagnóstico histórico post-selección

Calibration partition, primera T2 por lead:

- AUC: 0.543
- AP: 0.542
- prevalencia: 0.508
- AP/prevalencia: 1.069
- Lift@10%: 1.147x
- Brier: 0.249

Esto **no** es el gate prospectivo porque la política de features ya fue elegida usando este histórico.

## Feature policy

Bloqueados:

- calendario/progreso;
- prior_searches;
- Availability completa dentro de LeadQuality;
- broker prior;
- current-state Spot inseguro por el pipeline base.

T0/T1 quedan neutrales. Sólo T2 tiene artifact predictivo.

## Gate real

Ver `prospective_gate.json`.

El primer gate válido empieza después del freeze y exige al menos 500 leads maduros first-T2, AUC >=0.55 con lower CI >0.50, AP/prevalencia >=1.05, Lift@10 >=1.10 y timestamp de scheduled_visit >=99.5%.

No se relajarán thresholds después de mirar outcomes.
