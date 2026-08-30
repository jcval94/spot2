# Revisión de cierre

**Estado:** ACTIVE.

## Ya resuelto

- target predictiva de 30 días;
- semántica de censoring/ambiguous event time;
- primary outcome causal lead-level;
- unidad de randomización;
- power/MDE;
- regla SHIP/NO-SHIP/INCONCLUSIVE;
- exclusión de señales inestables/no robustas principales.

## Blockers

1. ejecutar/congelar E029 release candidate drift-sanitized;
2. aplicar el gate prospectivo E029 en una cohorte realmente posterior al freeze;
3. congelar model/calibrator/schema/policy hashes;
4. ejecutar A/A productivo con timestamp backend >=99.5%;
5. sólo entonces abrir E028.

## Refinamientos opcionales

- cerrar la decisión sobre price totals con una cohorte adicional;
- decidir por parsimonia si `prior_inquiries` permanece;
- añadir close_90d/revenue_90d cuando exista ground truth productivo.

La línea no se cierra todavía porque el tratamiento que alimentará el RCT aún no superó el gate temporal final.


E029 separa explícitamente el build histórico del gate prospectivo para evitar llamar "unseen" a datos ya utilizados durante E021–E027.
