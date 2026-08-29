# EV-009 — EDA profundo

**Estado de evidencia:** empírica, descriptiva + detección no supervisada outcome-free.

**Experimento:** [eda_profundo](../eda_profundo/)

## Ejecución reproducible validada

- GitHub Actions: https://github.com/jcval94/spot2/actions/runs/33279098644
- Job de EDA: éxito.
- Validación de outputs: éxito.
- Commit de resultados reproducibles: `2ce23b285fd3bfbe4bc4843ab9a85b6c0904451d`.
- Hidden outcomes: no usados.

La versión narrativa final fue revalidada posteriormente por el workflow de EDA profundo en el run:
https://github.com/jcval94/spot2/actions/runs/33279216104

## Alcance

Profundiza el EDA general previo al feature engineering del Modelo 3.

No entrena un modelo supervisado, no usa outcomes ocultos y no elimina observaciones.

El EDA general realizado previamente en esta conversación fue migrado íntegramente a:

- [base_eda](../eda_profundo/base_eda/)

## Evidencia fuente

- [Hallazgos](../eda_profundo/FINDINGS.md)
- [README y metodología](../eda_profundo/README.md)
- [Script reproducible](../eda_profundo/run_deep_eda.py)
- [Spec](../eda_profundo/experiment_spec.json)
- `eda_profundo/results/` — tablas reproducibles generadas por la ejecución.
- `eda_profundo/figures/` — 20 histogramas y diagnósticos visuales.
- `base_eda/` — EDA general previo migrado a la estructura gobernada.

## Hallazgos cuantitativos principales

### Drift / cohortes

El número total de inquiries por lead se mantiene aproximadamente en 4.2–4.8, pero las inquiries dentro de 30 días aumentan de **1.37 por lead en 2025-01** a **4.42 en 2026-06**.

La mediana de tiempo a primera inquiry cae de **7.82** a **2.31 días** y el proxy 30d pasa de 20.1% a 56.5%.

**Evidencia:** `results/cohort_dynamics.csv`.

### Clipping / generación sintética

- `requested_area / spot_area ≈ 0.30`: **35.53%**.
- `requested_area / spot_area ≈ 5.00`: **21.37%**.
- requested rent exactamente igual al max rent del lead: **25.16%**.
- requested sale exactamente igual al max sale del lead: **24.75%**.
- spot total price es prácticamente `area × price_sqm`: p99 de error relativo **5.05e-7** en renta y **2.83e-9** en venta.

**Evidencia:** `results/deterministic_relationships.csv`.

### Colas y outliers

Áreas, precios totales, mantenimiento e historial previo presentan colas muy largas. En varias variables el criterio Tukey marca porcentajes de un dígito alto o >10%, incluso dentro de sector × modalidad.

Esto es incompatible con interpretar mecánicamente “outlier = registro malo”.

**Evidencia:** `results/numeric_summary.csv`, `results/stratified_outliers.csv`.

### Isolation Forest

Se ejecuta con `contamination=0.03` sólo como diagnóstico y estratificado por sector × modalidad.

Espacios outcome-free:

- Lead: información T0; excluye `lead_score_internal`.
- Spot: atributos estáticos; excluye current-state/leakage fields.
- Inquiry: información conocida en `inquiry_at`; excluye respuesta del broker.

Resultado oficial:

- **155** lead flags.
- **94** spot flags.
- **685** inquiry flags.

Solapamiento con algún extremo univariado dentro del régimen:

- Lead: **25.8%** flags vs **3.7%** no flags.
- Spot: **46.8%** vs **5.2%**.
- Inquiry: **41.9%** vs **3.7%**.

Sensibilidad del anomaly score frente a scheduled_visit, inspeccionada sólo después del fit:

- top 1%: **17.95%** vs **19.94%** en el resto;
- top 3%: **19.12%** vs **19.94%**;
- top 5%: **19.38%** vs **19.94%**;
- top 10%: **19.52%** vs **19.96%**.

**Interpretación:** Isolation Forest identifica rareza multivariable, pero no una población de oportunidad y no justifica borrar filas.

**Evidencia:** `results/iforest_summary.csv`, `results/iforest_univariate_overlap.csv`, `results/iforest_proxy_tail_diagnostic.csv`.

### Market Context

- 72 claves geo-sector.
- 30 meses globales.
- 3–12 meses observados por clave.
- mediana 7.
- **0 claves completas**.

**Interpretación:** es un panel rotatorio/incompleto; el bajo coverage exacto del EDA base es estructural.

**Evidencia:** `results/market_panel_coverage.csv`.

### Availability

- **90.27%** de spots cambia de disponibilidad al menos una vez.
- mediana 4 transiciones.
- mediana 10 snapshots.
- separación entre snapshots: mediana **21 días**, p95 **97**, p99 **155**, máximo **319**.

**Interpretación:** Availability es estado temporal y además requiere medir staleness/edad del snapshot.

**Evidencia:** `results/availability_trajectories.csv`, `results/availability_snapshot_gap_summary.csv`.

### Compatibilidad

La tasa de scheduled_visit cambia poco por match geográfico simple (~1 pp) y por buckets de ratios área/presupuesto. Un ratio económico cercano a 1 no resulta consistentemente privilegiado.

**Interpretación:** el proxy sintético está débilmente acoplado a una noción intuitiva simple de fit. Esto es consistente con el bajo lift global de matching observado en EV-005/EV-006.

**Evidencia:** `results/match_bucket_rates.csv`.

### Current-state Spot

El fin observable es 2026-07-13.

- **373 spots (12.43%)** tienen `days_on_market` mayor al tiempo transcurrido desde `created_at` hasta ese fin observable.
- 17 implican una fecha >365 días después del fin observado.
- p99 del desfase: **+308 días**.
- máximo: **+694 días**.
- `spots.total_inquiries` coincide exactamente con el conteo de inquiries observable sólo en **7.07%** de spots.

**Interpretación:** `days_on_market`, `total_inquiries`, `total_views` e `is_active` deben seguir bloqueados para scoring histórico salvo reconstrucción point-in-time.

**Evidencia:** `results/current_state_temporal_consistency.csv`.

### Relaciones seleccionadas

- `prior_searches` vs `prior_inquiries`: **r=-0.00495**.
- Spot total_views vs total_inquiries: **r=0.90385**.
- log(area) vs log(rent total): **r=0.91829**.
- log(area) vs log(sale total): **r=0.91340**.
- urgency vs broker_response_hours: **r=0.01154**.

**Evidencia:** `results/selected_correlations.csv`.

### Broker

Con soporte >=50 inquiries, las tasas descriptivas abarcan **9.86%–32.79%**.

**Caveat:** esta dispersión mezcla composición de cartera, geografía, inventario, tiempo y lead mix; no es un efecto causal del broker.

### Missingness

`urgency_days` falta ~30–31% de forma muy similar por canal/respuesta. `broker_response_hours` falta ~15% en todas las categorías de respuesta.

Scheduled_visit casi no cambia por missingness:

- urgency presente 19.98% vs missing 19.76%;
- response hours presente 19.93% vs missing 19.81%.

**Evidencia:** `results/missingness_semantics.csv`.

## Leakage / validación

- hidden outcomes: no usados;
- `lead_score_internal`: excluido del Isolation Forest de leads;
- `broker_response` y `broker_response_hours`: excluidos del Isolation Forest de inquiries;
- `days_on_market`, `total_views`, `total_inquiries`, `is_active`: excluidos del Isolation Forest de Spot;
- Availability se estudia como trayectoria y gaps;
- Market Context se estudia como panel;
- scheduled_visit sólo se consulta después del anomaly fit como diagnóstico descriptivo;
- Isolation Forest se ajusta por sector × modalidad para no llamar anomalía a una escala normal de otro régimen.

## Qué demuestra / qué no

**Demuestra:**

- drift temporal del proceso de interacción;
- clipping y redundancias sintéticas;
- colas y regímenes que vuelven peligrosa la eliminación automática de outliers;
- naturaleza dinámica y potencialmente stale de Availability;
- incompletitud estructural del panel Market Context;
- incoherencia temporal de current-state Spot fields;
- baja relación cruda entre simple fit y el proxy;
- heterogeneidad descriptiva de broker;
- semántica no equivalente de `prior_searches` y `prior_inquiries`.

**No demuestra:**

- causalidad;
- qué transformaciones finales deben quedarse;
- que los outliers deban excluirse;
- que el broker cause su tasa observada;
- que el matching real sea irrelevante;
- que toda rareza sea error de datos.

## Descubrimientos relacionados

- [D013](../conocimiento_agregado/DESCUBRIMIENTOS.md#d013--el-drift-temporal-contiene-compresión-de-interacción)
- [D014](../conocimiento_agregado/DESCUBRIMIENTOS.md#d014--el-dataset-contiene-clipping-y-redundancias-sintéticas)
- [D015](../conocimiento_agregado/DESCUBRIMIENTOS.md#d015--los-outliers-son-mayormente-colas-de-régimen-no-suciedad-demostrada)
- [D016](../conocimiento_agregado/DESCUBRIMIENTOS.md#d016--market-context-es-un-panel-incompleto)
- [D017](../conocimiento_agregado/DESCUBRIMIENTOS.md#d017--availability-es-un-estado-dinámico)
- [D018](../conocimiento_agregado/DESCUBRIMIENTOS.md#d018--el-proxy-premia-débilmente-la-compatibilidad-intuitiva)
- [D019](../conocimiento_agregado/DESCUBRIMIENTOS.md#d019--los-agregados-actuales-de-spot-no-reconstruyen-una-historia-temporal-coherente)
- [D020](../conocimiento_agregado/DESCUBRIMIENTOS.md#d020--prior_searches-y-prior_inquiries-no-son-dos-versiones-de-la-misma-historia)
- [D021](../conocimiento_agregado/DESCUBRIMIENTOS.md#d021--broker-muestra-heterogeneidad-descriptiva-todavía-no-efecto-broker)
