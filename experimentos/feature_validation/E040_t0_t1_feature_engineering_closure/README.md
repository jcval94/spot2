# E040 — Cierre de Feature Engineering T0/T1

## Estado

**CLOSED / DECISION-READY WITH EXPLICIT REOPEN CONDITIONS.**

Este artifact no añade un nuevo modelo. Evalúa si, después de E020–E039, existe trabajo offline pendiente que sea necesario para considerar cerrada la línea T0/T1.

## Conclusión

**No existe un blocker metodológico pendiente que justifique seguir iterando con las mismas columnas y los mismos periodos.**

La línea debe cerrarse con las siguientes decisiones:

### T0

- LeadQuality propensity: `NEUTRAL_EVIDENCE_BACKED`.
- Search Need / specificity: conservar como representación explicativa/operativa.
- No seguir buscando lift mediante nuevas combinaciones de las mismas columnas.

### T1

- LeadQuality propensity: `NEUTRAL_EVIDENCE_BACKED`.
- Dynamic Need / PH / LOC / Lead×Spot fit: conservar para matching/routing experimental.
- No promover clusters a LeadQuality sólo por interpretabilidad.

### T2

- mantener candidato E029 sujeto a prospective gate.

## Por qué puede cerrarse

Se probaron de manera gobernada:

- transformaciones de escala;
- specificity/completeness;
- Search Need;
- Dynamic Need;
- soft clusters;
- centroid distances;
- Physical/Location;
- semantic interactions;
- Lead×Spot directional fit;
- missingness;
- frequency encoding;
- quantile bins;
- geo/inventory-relative;
- target encoding temporal suavizado.

Además:

- target E028 está congelada;
- ABT E030 pasó validación reproducible;
- test E030 ya fue consumido one-shot por E032/E033;
- rolling development E035–E037 no mostró recuperación robusta;
- continuar buscando combinaciones sobre el mismo histórico aumenta research-overfitting.

## Pendientes que NO bloquean el cierre

### Datos futuros

- prospective gate E029;
- A/A productivo E028;
- nueva cohorte independiente.

### Nuevas fuentes

- raw inquiry text → E039;
- geo preferida canónica;
- effective-dated market/inventory context;
- true commercial close/lease outcome.

Estos son **criterios de reapertura**, no trabajo incompleto de la línea actual.

## Regla de reapertura

Reabrir T0/T1 sólo si ocurre al menos uno:

1. nueva fuente con información genuinamente no contenida en E030;
2. nueva target comercial mejor alineada con negocio;
3. nueva cohorte temporal independiente;
4. temporalidad point-in-time nueva para Market/Inventory.

No reabrir sólo para:

- otro K;
- otra combinación de clusters;
- más cruces categóricos;
- otro target encoding sobre los mismos periodos;
- tuning extensivo del mismo feature space.

## Resultado de la revisión

**Ready to close.**


## Handoff final

El punto de entrada recomendado para revisar esta línea después del cierre es:

- [Flujo completo](../../registro_flujo/feature_engineering_t0_t1/README.md)
- [Arquitectura final](../../registro_flujo/feature_engineering_t0_t1/ARQUITECTURA_FINAL.md)
- [Checklist de cierre](../../registro_flujo/feature_engineering_t0_t1/CHECKLIST_CIERRE.md)
- [Manifest final](../../registro_flujo/feature_engineering_t0_t1/FINAL_STATE.json)

Estos artifacts son la referencia oficial si se propone reabrir T0/T1.
