# E038 — Stage-aware Feature Policy v2

## Decisión

Los experimentos E031–E037 cambian el significado de “neutral”.

T0/T1 ya no están neutrales por prudencia provisional; **LeadQuality neutral está respaldado empíricamente con los datos actuales**.

Pero neutralidad de LeadQuality no significa que el sistema ignore esas etapas.

### T0

- LeadQuality propensity: neutral.
- Search Need y specificity: representación activa para explicación, candidate generation y reglas operativas, no para ordenar por probabilidad de visita.

### T1

- LeadQuality propensity: neutral.
- Dynamic Need, Need transition, PH/LOC y Lead×Spot fit: representación activa para matching/routing experimental.
- No convertir pockets exploratorios en multiplicadores.

### T2

- LeadQuality: candidato E029 drift-sanitized.
- Activación sólo después del prospective gate.

## Por qué se congela

Se probaron:

- scale/log/specificity;
- Search Need;
- Dynamic Need;
- soft cluster distances;
- PH/LOC;
- semantic interactions;
- missingness;
- categorical frequency;
- robust quantile bins;
- inventory-relative;
- geo distance;
- temporally-smoothed target encoding.

T0 no produjo señal robusta. T1 mostró sólo señales débiles/inestables y ninguna pasó el gate.

Seguir combinando estas mismas columnas contra los mismos periodos aumentaría el riesgo de research overfitting.

## Qué sí justifica reabrir T0/T1

1. nueva fuente informativa (texto, firmografía, intención explícita, geo canónica);
2. target comercial superior a scheduled_visit;
3. nueva cohorte independiente;
4. features de mercado/inventario con effective time correcto.

La política machine-readable vive en FEATURE_POLICY_V2.json.
