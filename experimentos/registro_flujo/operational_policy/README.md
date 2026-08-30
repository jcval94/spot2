# FL-004 — Operational threshold + Inventory Availability probability

**Estado:** CLOSED / DECISION-READY.

## Pregunta original

Cerrar tres gaps del assessment:

1. threshold/capacidad;
2. threshold final;
3. P(availability) explícita.

## Respuesta actual

- T0: no high-priority gate.
- T1: top 15% dentro de etapa.
- T2: top 15% dentro de etapa.
- Threshold final: P85 stage-relative.
- P(availability): probabilidad a 30 días basada en estado backward-as-of y transición histórica por sector; para un lead se toma el máximo sobre su pool compatible/fallback.

## Por qué está cerrado

La política usa evidencia OOF temporal existente, agrega una frontera de capacidad explícita y valida Availability con 4 ventanas temporales y purge de 30 días. No queda una decisión pendiente para estos tres puntos.

El Lead Opportunity Score end-to-end y fallback@K son una fase distinta y no forman parte del cierre de FL-004.

## Navegación

- [CRONOLOGIA](CRONOLOGIA.md)
- [DECISIONES](DECISIONES.md)
- [TRAZABILIDAD](TRAZABILIDAD.md)
- [INCIDENCIAS_Y_CORRECCIONES](INCIDENCIAS_Y_CORRECCIONES.md)
- [CIERRE](CIERRE.md)
- [EV-019](../../Evidencias/EV-019_operational_threshold_availability.md)
