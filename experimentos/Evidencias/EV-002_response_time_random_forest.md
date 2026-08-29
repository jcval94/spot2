# EV-002 — Response-time Random Forest

**Estado de evidencia:** empírica, principalmente diagnóstica.

**Experimento:** [response_time_random_forest](../response_time_random_forest/)

## Evidencia fuente

- [README](../response_time_random_forest/README.md)
- [Hallazgos preliminares](../response_time_random_forest/preliminary_findings.md)
- [Código canónico](../response_time_random_forest/run_experiment.py)
- Resultados regenerables en `../response_time_random_forest/results/`.

## Resultado central

En la réplica multivariable inmediata, añadir response time no mejora AUC y su permutation importance es negativa/cercana a cero.

En el target posterior a primera respuesta, AUC puede subir ligeramente, pero la permutation importance sigue esencialmente en cero y el efecto contrafactual modelado 2h→36h es pequeño.

## Caveats

- `broker_response_hours` es post-inquiry: no es feature válida T0/T1.
- Importancia MDI de Random Forest no equivale a señal estable.
- No es prueba causal del SLA.

**Descubrimiento:** [D002](../conocimiento_agregado/DESCUBRIMIENTOS.md#d002--response-time-señal-operacional-no-driver-robusto).
