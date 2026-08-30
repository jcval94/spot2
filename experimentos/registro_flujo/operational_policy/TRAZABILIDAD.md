# Trazabilidad — FL-004

| Pregunta | Fuente | Evidencia | Discovery | Decisión |
|---|---|---|---|---|
| ¿Qué modelo de Lead Quality usar? | modelo_3 E006/E007 | EV-011 / EV-012 | arquitectura vigente | pooled CatBoost + stage + trajectory |
| ¿Qué capacidad usar? | E019 threshold frontier | EV-019 | D062 | P85 / top15 en T1/T2 |
| ¿Debe T0 priorizar? | E019 threshold frontier | EV-019 | D062 | no priority gate |
| ¿Cómo expresar Availability? | E019 availability CV | EV-019 | D063 | P(available within 30d) |
| ¿Puede usarse futuro? | leakage review | EV-019 | D063 | futuro sólo en y; purge 30d |
| ¿Usar days_until_available? | delay diagnostic | EV-019 | D063 | no como probability shaper |

Ruta principal: [E019](../../E019_operational_threshold_availability/).
