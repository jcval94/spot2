# Entregable 1 — EDA final

Este directorio es el **entry point oficial** del Entregable 1 del assessment de Spot2.

## Documento principal

➡️ **[Leer EDA_FINAL.md](EDA_FINAL.md)**

El documento está diseñado para poder evaluarse sin recorrer toda la investigación. Convierte los análisis de Codexway, experimentos y AssessmentSol1 en una sola narrativa de negocio, temporalidad, calidad de datos y decisiones.

## Jerarquía de evidencia

- **Codexway = autoridad final.** Sus contratos, cifras y decisiones prevalecen.
- **experimentos = evidencia experimental.** Se usa para challengers, resultados negativos, sensibilidad e hipótesis históricas.
- **AssessmentSol1 = auditoría metodológica.** Se usa para PIT correctness, leakage, drift, missingness y cuantificación complementaria.

Las métricas de poblaciones o targets incompatibles **no se combinan**.

## La historia en seis puntos

1. **T1 es el scoring moment principal:** primera inquiry, después de persistir el request y antes de broker response.
2. **La inquiry refina la necesidad:** área y presupuestos expresados en T1 agregan información respecto del intake.
3. **Retail tiene la presión demanda/oferta más clara:** +5.89 pp de share de demanda sobre share de catálogo en el clean-room DEVELOPMENT.
4. **El gran drift está en Inventory:** Availability coverage y candidate depth cambian mucho más que el mix marginal de leads.
5. **UNKNOWN no es UNAVAILABLE:** cobertura, freshness y serviceability se mantienen como conceptos distintos.
6. **La investigación de clusters produjo conocimiento, no reglas:** los pockets históricos permanecen como hipótesis; Codexway no confirma celdas tras multiplicidad.

## Estructura

- [EDA_FINAL.md](EDA_FINAL.md) — narrativa final y conclusiones.
- [REFERENCIAS.md](REFERENCIAS.md) — mapa de evidencia y trazabilidad.
- [VALIDACION.md](VALIDACION.md) — QA final, reconciliación de cifras y control de autoridad.
- [figuras/](figuras/) — seis visualizaciones autocontenidas en SVG.
- [tablas/](tablas/) — resúmenes CSV auditables.

### Figuras

1. [Demanda vs oferta por sector](figuras/01_demanda_vs_oferta_sector.svg)
2. [Target T1 vs coverage de Availability](figuras/02_target_vs_coverage_temporal.svg)
3. [Candidate depth temporal](figuras/03_candidate_depth_temporal.svg)
4. [Refinamiento de área T0→T1](figuras/04_refinamiento_area.svg)
5. [Market Context por sector](figuras/05_market_context_sector.svg)
6. [Frescura del inventario](figuras/06_frescura_inventario.svg)

### Tablas

1. [Resumen de fuentes](tablas/00_resumen_fuentes.csv)
2. [Métricas EDA clave](tablas/01_metricas_eda_clave.csv)
3. [Hallazgos → decisiones](tablas/02_hallazgos_decisiones.csv)
4. [Fuentes integradas](tablas/03_fuentes_integradas.csv)

## Lectura rápida para evaluación

Si sólo hay cinco minutos:

1. leer el [Resumen ejecutivo](EDA_FINAL.md#resumen-ejecutivo);
2. revisar [Demanda vs oferta](EDA_FINAL.md#4-demanda-vs-oferta-retail-es-la-presion-relativa-mas-clara);
3. revisar [Availability](EDA_FINAL.md#10-availability-cobertura-frescura-y-disponibilidad-son-tres-conceptos-distintos);
4. revisar [Segmentación y pockets](EDA_FINAL.md#15-segmentacion-y-clustering-conocimiento-acumulado-no-etiquetas-magicas);
5. terminar con [Hallazgo → Evidencia → Implicación → Decisión](EDA_FINAL.md#23-tabla-final--hallazgo--evidencia--implicacion--decision).

## Alcance

Este paquete corresponde **únicamente al Entregable 1 — EDA**. No crea ni modifica los entregables 2–8.
