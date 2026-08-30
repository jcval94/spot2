# EV-013 — Semantic profiles + dynamic need + clean broker + hierarchical matching

**Estado:** diseño registrado; resultados empíricos pendientes de la primera corrida reproducible.

Experimentos:

- [E008 Behavioral Persona](../matching_profiles_v4/specs/E008_behavioral_persona.json)
- [E009 Dynamic Need T1](../matching_profiles_v4/specs/E009_dynamic_need_t1.json)
- [E010 Clean Broker Profiles](../matching_profiles_v4/specs/E010_clean_broker_profiles.json)
- [E011 Hierarchical Matching](../matching_profiles_v4/specs/E011_hierarchical_matching.json)
- [E012 Dynamic Need Strong Baseline](../matching_profiles_v4/specs/E012_dynamic_need_strong_baseline.json)
- [E013 Balanced Broker Profiles](../matching_profiles_v4/specs/E013_balanced_broker_profiles.json)
- [E014 Hierarchical Matching v2](../matching_profiles_v4/specs/E014_hierarchical_matching_v2.json)
- [E015 Broker Service](../matching_profiles_v4/specs/E015_broker_service_profile.json)
- [E016 Dynamic + Service Hierarchy](../matching_profiles_v4/specs/E016_dynamic_service_hierarchy.json)

## Objetivo

Resolver los cuatro pendientes de segmentación identificados tras EV-010 sin mezclar cambios:

1. separar adquisición de madurez conductual;
2. representar Need como estado T0→T1;
3. reconstruir Broker sin `broker_response_hours`;
4. probar compatibilidad jerárquica sobre los nuevos perfiles.
5. ramificar de vuelta al baseline fuerte cuando una mejora intermedia perjudique el resultado.
6. exigir balance explícito en Broker y reintentar la jerarquía sólo sobre la rama fuerte.

## Guardrails

- mismo future test que E006/E007;
- clustering outcome-free;
- mismo Logistic Regression en toda la escalera;
- Dynamic Need excluye weekday;
- Broker excluye response_hours;
- service outcomes de Broker sólo usan historia anterior al profile cutoff;
- availability sigue point-in-time;
- celdas locales son exploratorias y no seleccionan el modelo.

## Descubrimientos relacionados

- [D038–D046](../conocimiento_agregado/DESCUBRIMIENTOS.md)
