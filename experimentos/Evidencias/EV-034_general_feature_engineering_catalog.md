# EV-034 — General Feature Engineering catalog

**Estado:** catálogo gobernado.

[E034](../feature_validation/E034_general_feature_engineering_catalog/)

El catálogo separa:

- TESTED_E031;
- NEXT_CHALLENGER;
- ROUTING_ONLY;
- POLICY_GUARDRAIL;
- BLOCKED/REJECTED;
- DATA_GAP.

Siguientes challengers priorizados:

1. missingness_as_signal;
2. rolling_behavior_velocity;
3. lead_preference_entropy;
4. price_relative_to_local_inventory;
5. geo_distance_to_preference_centroid;
6. target_encoded_high_cardinality, sólo con encoding temporal/cross-fitted.

Bloqueados/rechazados:
- Behavioral Persona como primary score;
- Broker Supply cluster;
- Market Context sin effective time;
- raw calendar/progress clocks;
- prior_searches.

Fuente: [feature_engineering_catalog.csv](../feature_validation/E034_general_feature_engineering_catalog/results/feature_engineering_catalog.csv).


## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
