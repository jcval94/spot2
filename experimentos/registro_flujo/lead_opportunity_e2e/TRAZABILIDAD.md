# Trazabilidad — FL-005

| Pregunta | Evidencia | Discovery | Decisión |
|---|---|---|---|
| Lead Quality final | EV-012 / E007 trajectory | arquitectura modelo_3 | pooled CatBoost + stage + trajectory |
| Threshold | EV-019 | D062 | P85 T1/T2 |
| P(availability) | EV-019 | D063 | probabilidad inventory a 30d |
| Fallback final | EV-020 | D064 | hasta K=3 bounded |
| Relevance @K | EV-020 | D065 | behavioral hit sólo diagnóstico |
| Score combinado | EV-020 | D066 | Quality × Inventory |
| Evaluación conjunta | EV-020 | D067 | joint_success + conversion guardrail |
