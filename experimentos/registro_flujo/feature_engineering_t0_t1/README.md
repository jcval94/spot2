# Flujo — Feature Engineering y recuperación T0/T1

**Estado:** CLOSED / DECISION-READY.

## Pregunta original

¿Podemos recuperar señal útil en T0 y T1 sin depender de clocks/progreso afectados por drift, usando mejor Feature Engineering, segmentación y representación semántica?

## Respuesta final

Con los datos actuales:

- **T0 LeadQuality:** `NEUTRAL_EVIDENCE_BACKED`.
- **T1 LeadQuality:** `NEUTRAL_EVIDENCE_BACKED`.
- **T0/T1 semántica:** sigue activa para explicación/matching/routing.
- **T2 LeadQuality:** candidato E029 pendiente prospective gate.

No se cierra porque “no quisimos seguir”; se cierra después de múltiples familias de FE y validaciones temporales sin recuperación robusta.

## Navegación

- [Cronología](CRONOLOGIA.md)
- [Decisiones](DECISIONES.md)
- [Trazabilidad](TRAZABILIDAD.md)
- [Cierre](CIERRE.md)
- [Arquitectura final](ARQUITECTURA_FINAL.md)
- [Checklist de cierre](CHECKLIST_CIERRE.md)
- [Estado final machine-readable](FINAL_STATE.json)
- [EV-030 — ABT definitiva](../../Evidencias/EV-030_definitive_abt.md)
- [EV-040 — cierre](../../Evidencias/EV-040_feature_engineering_closure.md)
