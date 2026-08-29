# External geographic enrichment candidates

The provided data supports several safe joins without inventing postal codes.

## Existing join keys

Lead level:
- preferred_state
- preferred_municipality
- preferred_corridor

Spot level:
- state
- municipality
- settlement
- corridor
- region
- lat / lon

Postal code is not present.

## Candidate external sources

| Source | Join level | Candidate features | Notes |
|---|---|---|---|
| INEGI Census / indicators | municipality | population, density, labor force, economic structure, growth | Prefer official municipality codes after building a stable crosswalk |
| INEGI DENUE | coordinates / municipality | establishment density, sector mix, nearby business counts | Particularly useful for office/retail/industrial demand context |
| SEPOMEX postal code catalog | settlement + municipality + state | postal code, locality normalization | Stronger for spots than leads because leads do not include settlement/address |
| OpenStreetMap | lat/lon | transit/road access, POI density, distance to highways/airports | Snapshot/version must be recorded for reproducibility |
| CONAPO | municipality/state | population projections, urbanization/growth | Slow-moving context |
| Banxico | national/state-time where available | rate environment, financing conditions | Join as-of lead/inquiry date, never using future observations |

## Recommended sequence

1. First prove that existing time-safe market/geographic context adds incremental lift.
2. Add municipality-level INEGI/DENUE features because the lead already has municipality.
3. Add coordinate-based accessibility features for spots.
4. Only add postal-code features if a reliable historical location-to-CP mapping is available.
5. Re-run the same temporal validation and keep only features that improve ranking/calibration without creating instability.

## Leakage rule

For a historical lead created at time t, the external feature value must have been observable at or before t. Record source date, retrieval date and effective date separately.
