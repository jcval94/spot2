# Decisiones

## D1 — No usar clocks para “rescatar” T1

La mejora T1 inicial dependía materialmente de variables de tiempo/progreso afectadas por non-stationarity.

Decisión: clocks = audit-only.

## D2 — No asumir que clustering interpretable implica lift

Dynamic Need/PH/LOC siguen siendo útiles como lenguaje de negocio y matching, pero no se promueven automáticamente a LeadQuality.

## D3 — Separar funciones del sistema

T0/T1 pueden ser semánticamente activos sin tener propensity score útil.

- LeadQuality: neutral.
- Matching/routing representation: activa.

## D4 — Consumir test una sola vez

E031 seleccionó con train/validation. E032/E033 consumieron E030 test.

Experimentos posteriores usan rolling development y no reclaman confirmación independiente.

## D5 — No seguir optimizando el mismo feature space

Después de E031–E037, más cruces/K/tuning sobre los mismos periodos elevan research-overfitting.

## D6 — E039 sólo con texto real

No se sintetiza un mensaje desde variables estructuradas para “probar” un LLM.

## D7 — Reapertura condicionada a información nueva

Reabrir sólo con:

- raw inquiry text;
- nueva target comercial;
- market/inventory effective-dated;
- geo preferida canónica;
- nueva cohorte independiente.
