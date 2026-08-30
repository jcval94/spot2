# Trazabilidad

| Pregunta | Experimento | Evidencia | Descubrimiento | Decisión |
|---|---|---|---|---|
| ¿Existe drift? | E020/E021 | EV-020/EV-021 | D060/D069 | Multi-cohorte obligatorio |
| ¿Los clocks explican el lift? | E022 | EV-022 | D069 | BLOCK E005/T1 crudo |
| ¿Cómo usar Availability? | E023 | EV-023 | D064/D070 | freshness guardrail |
| ¿Borrar outliers? | E024 | EV-024 | D062/D071 | conservar |
| ¿Quitar price totals? | E025 | EV-025 | D061/D072 | inconcluso |
| ¿Qué hacer con historial previo? | E026 | EV-026 | D067/D073 | retirar prior_searches |
| ¿Usar broker prior? | E027 | EV-027 | D068/D074 | no incluir |
| ¿Cuál es la target? | E028 | EV-028 | D076 | target con timestamp conocido |
| ¿Cómo evaluar causalmente? | E028 | EV-028 | D077 | A/B lead-level ITT |
| ¿Puede lanzarse ya? | E028 + siguiente candidato | EV-028 | D075 | no; falta release sanitizado |

Harness records: `experimentos/Evidencias/harness_records/E021_...` a `E027_...`.
