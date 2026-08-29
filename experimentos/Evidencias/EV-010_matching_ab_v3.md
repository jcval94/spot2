# EV-010 — Relational audit + Matching A/B v3

**Estado de evidencia:** diseño registrado; ejecución empírica en curso.

**Experimentos:**

- [E006 — Physical vs Location Spot](../matching_ab_v3/specs/E006_physical_location_spot.json)
- [E007 — Compatibility Routing](../matching_ab_v3/specs/E007_compatibility_routing.json)
- [Carpeta de la suite](../matching_ab_v3/)

## Precondición de calidad

La suite no acepta un resultado de modelado si falla un control crítico de:

- unicidad de claves;
- integridad referencial;
- cardinalidad de joins;
- conservación de filas;
- joins as-of de disponibilidad;
- consistencia temporal Lead/Spot → Inquiry;
- reglas de presupuesto/precio por modalidad;
- consistencia de respuesta y horas de respuesta;
- rangos básicos y completitud esperada.

Se registran por separado `relationship_checks.csv`, `content_consistency_checks.csv`, `column_completeness.csv` y `data_quality_summary.csv`.

## Diseño A/B offline

E006 y E007 usan A y B sobre exactamente las mismas filas, mismo target proxy, mismo train y mismo future test. El backtest mide asociación/poder predictivo, **no causalidad**.

## Diseño A/B online pre-registrado

- Unidad de randomización: `lead_id`.
- Asignación: 50/50 sticky.
- Bloqueo/estratificación: `search_sector × search_modality × user_type`.
- Primary outcome: al menos un `scheduled_visit` por lead dentro de 30 días.
- Análisis: intention-to-treat a nivel lead, horizonte fijo, 95% CI, sin optional stopping.
- Guardrails: sample-ratio mismatch, elegibilidad, cobertura/lag de availability, recomendaciones no disponibles, concentración de carga de brokers y no-result rate.
- Power: se calcula con la tasa lead-level observada y MDEs de 1–3 pp.

## Estado actual

Los artifacts numéricos y las conclusiones se completarán sobre esta misma evidencia después de la primera corrida exitosa de GitHub Actions.

## Descubrimientos relacionados

- [D023 — Separar Spot físico de localización](../conocimiento_agregado/DESCUBRIMIENTOS.md#d023--separar-spot-físico-de-localización)
- [D024 — Compatibility Routing](../conocimiento_agregado/DESCUBRIMIENTOS.md#d024--compatibility-routing-como-tratamiento-explícito)
