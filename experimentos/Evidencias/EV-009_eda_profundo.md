# EV-009 — EDA profundo

**Estado de evidencia:** empírica, descriptiva + detección no supervisada outcome-free.

**Experimento:** [eda_profundo](../eda_profundo/)

## Alcance

Profundiza el EDA general previo al feature engineering del Modelo 3.

No entrena un modelo supervisado, no usa outcomes ocultos y no elimina observaciones.

El EDA general realizado previamente fue migrado íntegramente a:

- [base_eda](../eda_profundo/base_eda/)

## Evidencia fuente

- [Hallazgos](../eda_profundo/FINDINGS.md)
- [README y metodología](../eda_profundo/README.md)
- [Script reproducible](../eda_profundo/run_deep_eda.py)
- [Spec](../eda_profundo/experiment_spec.json)
- `eda_profundo/results/` — tablas reproducibles generadas por la ejecución
- `eda_profundo/figures/` — histogramas y diagnósticos

## Hallazgos cuantitativos principales

### Drift / cohortes

El número total de inquiries por lead se mantiene aproximadamente en 4.2–4.8, pero las inquiries dentro de 30 días aumentan de ~1.37 por lead en 2025-01 a >4.1 en 2026-05/06.

La mediana de tiempo a primera inquiry cae de ~7.82 días a ~2.31 días.

**Evidencia:** `results/cohort_dynamics.csv`.

### Clipping / generación sintética

- `requested_area / spot_area ≈ 0.30`: ~35.5%.
- `requested_area / spot_area ≈ 5.00`: ~21.4%.
- requested rent exactamente igual al max rent del lead: ~25.1%.
- requested sale exactamente igual al max sale del lead: ~24.7%.
- spot total price es prácticamente `area × price_sqm`: p99 de error relativo ~5e-7 en renta y ~3e-9 en venta.

**Evidencia:** `results/deterministic_relationships.csv`.

### Colas y outliers

Áreas, precios totales, mantenimiento e historial previo presentan colas muy largas. En varias variables el criterio Tukey marca 7–13% o más de observaciones, incluso dentro de sector × modalidad.

Esto es incompatible con interpretar mecánicamente “outlier = registro malo”.

**Evidencia:** `results/numeric_summary.csv`, `results/stratified_outliers.csv`.

### Isolation Forest

Se ejecuta con `contamination=0.03` sólo como diagnóstico y estratificado por sector × modalidad.

Espacios:

- Lead: información T0; excluye `lead_score_internal`.
- Spot: atributos estáticos; excluye current-state/leakage fields.
- Inquiry: información conocida en `inquiry_at`; excluye respuesta del broker.

Una ejecución diagnóstica independiente encontró que aproximadamente:

- 80% de leads marcados;
- 99% de spots marcados;
- 65% de inquiries marcadas

también poseen algún extremo univariado dentro de su régimen.

Las inquiries anómalas no tienen mayor proxy: ~19.1% scheduled_visit vs ~19.9% en no marcadas.

**Interpretación:** Isolation Forest es útil para inspección multivariable, no para borrar filas ni como Opportunity Score.

### Market Context

- 72 claves geo-sector.
- 30 meses globales.
- 3–12 meses observados por clave.
- mediana ~7.
- 0 claves completas.

**Interpretación:** es un panel rotatorio/incompleto; el bajo coverage exacto del EDA base es estructural.

### Availability

- ~90.3% de spots cambia de disponibilidad al menos una vez.
- mediana ~4 transiciones.
- mediana ~10 snapshots.

**Interpretación:** Availability es estado temporal, no rasgo permanente de Spot.

### Compatibilidad

La tasa de scheduled_visit cambia poco por match geográfico simple (~1 pp) y por buckets de ratios área/presupuesto.

**Interpretación:** el proxy sintético está débilmente acoplado a una noción intuitiva simple de fit. Esto es consistente con el bajo lift global de matching observado en EV-005/EV-006.

### Broker

Con soporte >=50 inquiries, las tasas descriptivas observadas abarcan aproximadamente 9.9%–32.8%.

**Caveat:** esta dispersión mezcla composición de cartera, geografía, inventario, tiempo y lead mix; no es un efecto causal del broker.

## Leakage / validación

- hidden outcomes: no usados;
- `lead_score_internal`: excluido del Isolation Forest de leads;
- `broker_response` y `broker_response_hours`: excluidos del Isolation Forest de inquiries;
- `days_on_market`, `total_views`, `total_inquiries`, `is_active`: excluidos del Isolation Forest de Spot;
- Availability se estudia como trayectoria;
- Market Context se estudia como panel;
- scheduled_visit sólo se consulta después del anomaly fit como diagnóstico descriptivo.

## Qué demuestra / qué no

**Demuestra:**

- drift temporal del proceso de interacción;
- clipping y redundancias sintéticas;
- colas y regímenes que vuelven peligrosa la eliminación automática de outliers;
- naturaleza dinámica de Availability;
- incompletitud estructural del panel Market Context;
- baja relación cruda entre simple fit y el proxy.

**No demuestra:**

- causalidad;
- qué transformaciones finales deben quedarse;
- que los outliers deban excluirse;
- que el broker cause su tasa observada;
- que el matching real sea irrelevante.

## Descubrimientos relacionados

- [D013](../conocimiento_agregado/DESCUBRIMIENTOS.md#d013--el-drift-temporal-contiene-compresión-de-interacción)
- [D014](../conocimiento_agregado/DESCUBRIMIENTOS.md#d014--el-dataset-contiene-clipping-y-redundancias-sintéticas)
- [D015](../conocimiento_agregado/DESCUBRIMIENTOS.md#d015--los-outliers-son-mayormente-colas-de-régimen-no-suciedad-demostrada)
- [D016](../conocimiento_agregado/DESCUBRIMIENTOS.md#d016--market-context-es-un-panel-incompleto)
- [D017](../conocimiento_agregado/DESCUBRIMIENTOS.md#d017--availability-es-un-estado-dinámico)
- [D018](../conocimiento_agregado/DESCUBRIMIENTOS.md#d018--el-proxy-premia-débilmente-la-compatibilidad-intuitiva)
