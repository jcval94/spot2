# Cierre — FL-005

**Estado:** CLOSED / DECISION-READY.

## Checklist

- Lead Quality congelado: sí.
- Inventory Availability congelado: sí.
- Threshold/capacidad: sí.
- Fallback conceptual: sí.
- Fallback @K: sí, K=3.
- Fórmula de combinación: sí.
- Distribución del score: sí.
- Evaluación conjunta: sí.
- Guardrail conversión: sí.
- Leakage: PASS.
- Resultados negativos retenidos: sí.
- Evidencia y discoveries enlazados: sí.

## Decisión final

`Lead Opportunity Score = P_quality × P_inventory_top3`

Priorizar top 15% dentro de T1/T2.

Si el spot actual no está disponible, devolver hasta 3 alternativas bounded. Si no existe una alternativa defendible, NO_RESULT / revisión manual.

## Reapertura

Reabrir sólo si:

1. existe un log real de recomendaciones y clicks/visitas atribuibles;
2. Growth define otra capacidad operativa;
3. cambian las restricciones del producto;
4. nueva cohorte temporal contradice materialmente la decisión.

Optimización cosmética offline no es motivo suficiente para reabrir.
