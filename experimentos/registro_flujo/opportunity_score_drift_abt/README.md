# Research flow — Opportunity Score, drift y A/B definitivo

**Estado:** ACTIVE

## Pregunta original

¿Cómo convertir el Modelo 3 y los descubrimientos de Lead/Inquiry/Spot en una política de negocio defendible, temporalmente robusta y evaluable causalmente?

## Respuesta actual

1. El score dinámico tiene señal offline, pero una parte material —especialmente T1— está dominada por clocks/progreso sujetos a drift.
2. Availability debe separarse en estado y frescura; freshness es guardrail, no señal comercial demostrada.
3. Outliers no deben borrarse automáticamente.
4. `prior_searches` debe salir del candidato actual; broker prior no tiene lift robusto.
5. La target offline debe ser `target_scheduled_visit_30d(l,t)` con tiempo de evento conocido; eventos ambiguos por timestamp nunca se imputan 0.
6. La evaluación causal final debe ser lead-level, ITT y sistémica: `lead_scheduled_visit_30d_from_assignment`.
7. El protocolo A/B está pre-registrado, pero el Treatment permanece bloqueado hasta entrenar y validar un release candidate drift-sanitized.

## Por qué la línea sigue ACTIVE

La pregunta metodológica de target + diseño causal ya está resuelta. Falta una pieza científica antes de launch: construir el candidato sanitizado y demostrar que la señal residual —principalmente T2— se sostiene en una cohorte futura adicional.

## Navegación

- [CRONOLOGIA.md](CRONOLOGIA.md)
- [DECISIONES.md](DECISIONES.md)
- [TRAZABILIDAD.md](TRAZABILIDAD.md)
- [INCIDENCIAS_Y_CORRECCIONES.md](INCIDENCIAS_Y_CORRECCIONES.md)
- [CIERRE.md](CIERRE.md)

## Evidencia canónica

EV-020 a EV-028 bajo [Evidencias](../../Evidencias/).
