# FL-005 — Lead Opportunity Score + Fallback end-to-end

**Estado:** CLOSED / DECISION-READY.

## Pregunta original

Cerrar los cuatro gaps restantes del assessment:

1. fallback conceptual;
2. fallback final @K;
3. Lead Opportunity Score combinado;
4. evaluación end-to-end.

## Respuesta actual

- fallback: hasta K=3, bounded y point-in-time;
- score: P_quality × P_inventory_top3;
- capacidad: P85 dentro de T1/T2;
- objetivo conjunto: scheduled_visit_30d AND confirmed_serviceable;
- resultado final: +8 joint positives (+7.5%) a la misma capacidad en fold 4;
- guardrail: -10 conversion positives si se ignora serviceability.

## Por qué está cerrado

Los componentes ya estaban validados por separado. E020 define su interfaz, congela la política de recomendación, selecciona K sin usar fold 4 y evalúa el sistema bajo la capacidad operativa ya congelada.

Lo que queda es medición online/productización, no modelado offline faltante.

## Navegación

- [CRONOLOGIA](CRONOLOGIA.md)
- [DECISIONES](DECISIONES.md)
- [TRAZABILIDAD](TRAZABILIDAD.md)
- [INCIDENCIAS_Y_CORRECCIONES](INCIDENCIAS_Y_CORRECCIONES.md)
- [CIERRE](CIERRE.md)
- [EV-020](../../Evidencias/EV-020_lead_opportunity_fallback_e2e.md)
