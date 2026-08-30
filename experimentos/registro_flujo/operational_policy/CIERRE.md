# Cierre — FL-004

**Estado:** CLOSED / DECISION-READY.

## Criterios

- pregunta: respondida;
- scoring/target: congelados para esta decisión;
- leakage: PASS;
- validación temporal: sí;
- capacity frontier: sí;
- threshold final: sí;
- P(availability) explícita: sí;
- resultados negativos: retenidos;
- descubrimientos/evidencia: enlazados.

## Decisión final

1. T0: no high-priority gate.
2. T1: top 15% within-stage.
3. T2: top 15% within-stage.
4. Threshold: stage-relative P85.
5. P(availability): current available = 1; si no, transición histórica sectorial a 30d aprendida sólo con pasado maduro.
6. Lead availability: máximo sobre candidatos compatibles.

## No bloqueadores / siguiente fase

No reabrir FL-004 por optimización cosmética de threshold. Reabrir sólo si:

- Growth entrega una capacidad operacional real distinta;
- aparece nueva evidencia temporal que rompe la frontera;
- cambia la semántica de availability snapshots.

Lead Opportunity Score end-to-end y fallback@K pertenecen a integración posterior y no invalidan este cierre.
