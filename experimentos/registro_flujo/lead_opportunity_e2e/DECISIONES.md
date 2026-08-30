# Decisiones — FL-005

## D1 — K=3 como máximo

**CURRENT.**

Folds 1–3: full-list K3 60.8% vs K5 50.3%. K3 equilibra cobertura y utilidad operativa.

## D2 — No relajar indefinidamente

**CURRENT.**

El fallback no cruza estado, sector ni modalidad; área y presupuesto tienen límites. Si no hay candidato se emite NO_RESULT.

## D3 — No usar behavioral Hit@K como gate principal

**CURRENT.**

El spot histórico de scheduled_visit contradice con frecuencia sector/corredor y no es un log de exposición a recomendaciones.

## D4 — Fórmula multiplicativa

**CURRENT.**

`LOS = P_quality × P_inventory_top3`.

Es simple, monotónica e interpretable. No se declara probabilidad conjunta calibrada.

## D5 — Evaluar contra joint_success

**CURRENT.**

El sistema combinado debe medir conversión + serviceability. scheduled_visit puro se conserva como guardrail.

## D6 — Aceptar el tradeoff

**CURRENT.**

En fold 4, LOS gana +8 joint positives y pierde 10 conversion positives puros. Para el objetivo del assessment se prioriza el primer resultado.
