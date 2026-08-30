# Registro de flujo de investigación

Esta carpeta documenta **cómo evolucionan líneas completas de investigación** cuando atraviesan varios experimentos, decisiones y cambios de criterio.

No sustituye:

- `conocimiento_agregado/DESCUBRIMIENTOS.md`: qué se aprendió;
- `Evidencias/`: qué artifacts prueban cada hallazgo;
- cada carpeta de experimento: cómo se ejecutó un test concreto.

El registro de flujo responde otra pregunta:

> ¿Cómo pasamos de la pregunta inicial a la decisión actual, y por qué cambiamos de opinión?

## Líneas registradas

| Flujo | Estado | Decisión actual |
|---|---|---|
| [Modelo 3 — dynamic Lead Quality](modelo_3/) | **CLOSED / DECISION-READY** | pooled CatBoost + stage + trajectory como baseline operativo; especialistas tabulares como challengers |
| [FL-003 — Segmentación, perfiles y Matching](segmentation_matching/) | **CLOSED / DECISION-READY** | Persona + Need T0/T1 + Physical/Location; E007 global, BSV auxiliar; pockets requieren nueva evidencia |
| [Selección del caso de uso LLM](llm_use_case/) | **ACTIVE** | probar Semantic Inventory Quality contra Rules-only; Copilot/fallback quedan como opciones futuras, no como justificación principal |
| [Feature Engineering y recuperación T0/T1](feature_engineering_t0_t1/) | **CLOSED / DECISION-READY** | LeadQuality T0/T1 neutral con evidencia; capas semánticas activas; reabrir sólo con información/target/cohorte nueva |
| [Opportunity Score — drift, target y A/B](opportunity_score_drift_abt/) | **ACTIVE / PRE-REGISTERED** | target y protocolo causal congelados; E029 artifact T2 congelado, pendiente prospective gate + A/A productivo antes de tráfico real |

## Regla

Una línea multi-experimento debe registrar:

1. pregunta original;
2. hipótesis y bifurcaciones;
3. cronología de experimentos;
4. decisiones y qué evidencia las cambió;
5. resultados negativos/inconclusos;
6. incidencias metodológicas o de ingeniería que afectaron el diseño;
7. criterio explícito de cierre;
8. pendientes que son fase siguiente, no bloqueadores del cierre.
