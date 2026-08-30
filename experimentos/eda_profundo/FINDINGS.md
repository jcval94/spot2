# EDA profundo — hallazgos

## Resumen

Este análisis profundiza el EDA base sin entrenar el Modelo 3. La conclusión central es que **el dataset no debe tratarse como una tabla IID con outliers removibles**: contiene colas por régimen, paneles temporales incompletos, estados con staleness variable y varias restricciones sintéticas del generador.

## 1. El drift temporal contiene compresión de interacción

El total de inquiries por lead es relativamente estable entre cohortes, alrededor de 4.2–4.8.

Lo que cambia radicalmente es **cuándo** ocurren:

| Cohorte | Inquiries/lead totales | Inquiries <=30d/lead | Mediana primera inquiry | Proxy 30d |
|---|---:|---:|---:|---:|
| 2025-01 | 4.75 | 1.37 | 7.82 d | 20.1% |
| 2025-06 | 4.66 | 2.44 | 3.77 d | 36.7% |
| 2025-12 | 4.63 | 3.55 | 3.32 d | 46.2% |
| 2026-03 | 4.51 | 4.03 | 2.76 d | 53.4% |
| 2026-05 | 4.28 | 4.20 | 2.57 d | 57.7% |
| 2026-06 | 4.42 | 4.42 | 2.31 d | 56.5% |

**Lectura:** parte del poder aparente de variables como `days_from_lead_creation` puede provenir del mecanismo de generación/cohorte. La validación temporal no es opcional.

Evidencia: `results/cohort_dynamics.csv`, figuras 10–11.

## 2. Hay clipping explícito en la construcción de inquiries

### Área solicitada vs Spot

`requested_area_sqm / spot.area_sqm` tiene:

- **35.53%** de masa cerca de 0.30;
- **21.37%** cerca de 5.00;
- límites prácticamente fijados alrededor de 0.30 y 5.00.

### Presupuesto solicitado vs presupuesto máximo del lead

- Rent: **25.16%** de los casos con ambos valores son exactamente 100% del máximo del lead.
- Sale: **24.75%** son exactamente 100%.
- La distribución está fuertemente restringida hacia el rango alto del presupuesto declarado.

**Lectura:** estas variables contienen intención, pero también reglas del generador. No deben interpretarse como señales independientes puramente orgánicas.

Evidencia: `results/deterministic_relationships.csv`, figuras 08–09.

## 3. Precio total del Spot es casi redundante

En los registros con valores disponibles:

`price_total ≈ area_sqm × price_sqm`

El p99 del error relativo es:

- renta: **5.05e-7**;
- venta: **2.83e-9**.

**Implicación posterior:** usar simultáneamente área, precio/m² y precio total puede introducir redundancia casi determinista. Esto no decide aún la selección de features, pero sí exige ablation/regularización posterior.

## 4. Las distribuciones tienen colas fuertes y múltiples escalas

Ejemplos:

- Lead target area: mediana ~393 m², p95 ~1,479, p99 ~7,665, máximo ~9,962.
- Inquiry requested area: mediana ~484 m², p95 ~4,898, p99 ~12,774, máximo ~40,921.
- Spot area: mediana ~617 m², p95 ~15,562, p99 ~42,221, máximo ~136,403.
- Spot sale total: mediana ~19.8 M MXN, p99 ~677.6 M, máximo ~1.88 B.
- Maintenance: mediana ~10.4k, p99 ~379k, máximo ~1.67 M.
- Lead prior inquiries: mediana 1, p95 78, p99 145, máximo 199.

En varias variables el criterio Tukey marca porcentajes de un dígito alto o incluso >10%, aun dentro de sector × modalidad. Eso es demasiado para asumir que “outlier” equivale a error.

Evidencia: `results/numeric_summary.csv`, `results/stratified_outliers.csv`, figuras 01–07.

## 5. Isolation Forest es útil como lupa, no como limpiador ni score comercial

El detector se ajustó **sin outcome** y por régimen sector × modalidad:

- Lead: información T0 observable; excluye `lead_score_internal`.
- Spot: atributos estáticos; excluye `days_on_market`, `total_views`, `total_inquiries` e `is_active`.
- Inquiry: contenido observable en `inquiry_at`; excluye `broker_response` y `broker_response_hours`.
- contamination diagnóstica: 3%.

La ejecución oficial marca:

- 155 leads;
- 94 spots;
- 685 inquiries.

El solapamiento con algún extremo univariado dentro del mismo régimen es:

| Entidad | IF flag | No flag |
|---|---:|---:|
| Lead | **25.8%** | 3.7% |
| Spot | **46.8%** | 5.2% |
| Inquiry | **41.9%** | 3.7% |

Por tanto, el bosque sí añade información multivariable, pero una parte material de sus flags corresponde a colas ya visibles.

### Sensibilidad del anomaly score frente al proxy

| Cola más anómala | Scheduled visit | Resto | Delta |
|---|---:|---:|---:|
| top 1% | 17.95% | 19.94% | -1.99 pp |
| top 3% | 19.12% | 19.94% | -0.82 pp |
| top 5% | 19.38% | 19.94% | -0.56 pp |
| top 10% | 19.52% | 19.96% | -0.44 pp |

**Lectura:** no aparece una relación positiva ni monótona que permita reinterpretar “anomalía” como “oportunidad”. Tampoco hay justificación para eliminar filas automáticamente.

Evidencia: `results/iforest_summary.csv`, `results/iforest_*_anomalies.csv`, `results/iforest_univariate_overlap.csv`, `results/iforest_proxy_tail_diagnostic.csv`, figuras 14 y 20.

## 6. `prior_searches` y `prior_inquiries` parecen representar procesos distintos

- `prior_searches`: 34.5% es cero; mediana 2; p95 44; máximo 60.
- `prior_inquiries`: 44.4% es cero; mediana 1; p95 78; máximo 199.
- correlación Pearson: **-0.00495**.

Es llamativo porque los nombres sugieren historial relacionado, pero empíricamente casi no comparten variación lineal.

**Lectura:** no deben sumarse o combinarse mecánicamente como si fueran dos medidas equivalentes de “actividad histórica” sin validar antes su semántica.

Evidencia: `results/selected_correlations.csv`.

## 7. Availability es profundamente temporal y además puede estar stale

Sobre 3,000 spots:

- mediana: 10 snapshots;
- **90.27%** cambia de estado al menos una vez;
- mediana: 4 transiciones;
- sólo ~6.8% permanece siempre disponible;
- ~2.9% siempre no disponible.

Entre snapshots consecutivos:

- mediana: **21 días**;
- p95: **97 días**;
- p99: **155 días**;
- máximo: **319 días**.

Cuando el Spot no está disponible, `days_until_available` presenta también una cola larga.

**Lectura:** Availability debe tratarse como estado as-of y la **edad del snapshot** es parte del problema. “Último snapshot conocido” no equivale a “estado fresco”.

Evidencia: `results/availability_trajectories.csv`, `results/availability_snapshot_gap_summary.csv`, figura 13.

## 8. Market Context es un panel rotatorio/incompleto

- 72 claves geo-sector.
- 30 meses distintos globalmente.
- cada clave aparece sólo 3–12 meses;
- mediana 7 meses;
- **0 claves** cubren los 30 meses.

Esto explica la cobertura exacta ~23% del EDA base. Un forward-fill indiscriminado crearía información difícil de defender point-in-time.

Evidencia: `results/market_panel_coverage.csv`, figura 12.

## 9. Correlaciones que llaman la atención

- Spot `total_views` vs `total_inquiries`: **0.904**.
- log(area) vs log(rent total): **0.918**.
- log(area) vs log(sale total): **0.913**.
- `days_on_market` vs `total_views`: **0.670**.
- Market occupancy vs absorption days: **-0.448**.
- Market occupancy vs avg price/m²: **0.512**.
- Lead log(target area) vs log(max budget): ~0.60–0.63.
- Inquiry log(requested area) vs message length: ~**-0.012**.
- Urgency vs broker response hours: ~**0.012**.

**Lectura:** varios campos de Spot están fuertemente ligados por construcción/acumulación, mientras variables intuitivamente relacionadas dentro de Inquiry muestran prácticamente independencia.

Evidencia: `results/selected_correlations.csv`, figuras 17–18.

## 10. La compatibilidad intuitiva apenas mueve scheduled_visit

En crudo:

- mismo estado: ~20.7% vs 19.6%;
- mismo municipio: ~20.9% vs 19.7%;
- mismo corredor: ~20.8% vs 19.7%.

Los buckets de budget/spot price y requested area/spot area permanecen relativamente planos. El bucket de presupuesto cercano a 1 ni siquiera es consistentemente el mejor.

**Lectura:** este proxy sintético está débilmente acoplado a una noción simple de economic/geographic fit. Esto ayuda a explicar el lift limitado de los experimentos globales de matching.

**No demuestra:** que el matching real no sea útil en producción.

Evidencia: `results/match_bucket_rates.csv`, figura 15.

## 11. Existe heterogeneidad descriptiva de broker con soporte

Entre brokers con >=50 inquiries se observan tasas aproximadamente entre **9.86% y 32.79%**.

Eso es una dispersión material, pero puede mezclar:

- cartera;
- geografía;
- tipo de spot;
- lead mix;
- tiempo.

**Implicación:** merece experimentarse con perfiles históricos point-in-time y shrinkage, no con una tasa full-dataset interpretada como “calidad causal del broker”.

Evidencia: `results/broker_summary.csv`, figura 16.

## 12. `days_on_market` no es temporalmente coherente como reloj histórico

El final observable del dataset es 2026-07-13 17:35:37.

Si se interpreta literalmente:

`spot.created_at + days_on_market`

entonces:

- **373 spots (12.43%)** terminan después del final observable;
- 17 spots quedan a más de un año en el futuro;
- p95 de la diferencia frente al observation end: **+112 días**;
- p99: **+308 días**;
- máximo: **+694 días**.

Además, `spots.total_inquiries` coincide exactamente con el conteo observable de `inquiries` en sólo **7.07%** de los spots.

**Lectura:** estos campos deben seguir tratándose como current-state/synthetic aggregates, no como historia reconstruible en un timestamp pasado.

Evidencia: `results/current_state_temporal_consistency.csv`, figura 19.

## 13. El missingness de urgency y response hours parece poco informativo

`urgency_days` falta ~30–31% en prácticamente todos los canales y categorías de respuesta.

`broker_response_hours` falta ~15% tanto en accepted, rejected, scheduled_visit como no_response.

Las tasas de scheduled_visit son casi iguales:

- urgency presente: 19.98%; missing: 19.76%.
- response hours presente: 19.93%; missing: 19.81%.

**Lectura:** en este dataset no aparece una regla fuerte de missing-not-at-random para estos dos campos. Sigue siendo válido conservar indicadores de missingness durante los experimentos, pero el EDA no sugiere que sean señales dominantes.

Evidencia: `results/missingness_semantics.csv`.

## Conclusión para el siguiente paso

El feature engineering debería partir de estas reglas, sin implementarlas todavía aquí:

1. preservar tiempo/cohorte explícitamente;
2. preferir representaciones robust/log para variables de escala;
3. no eliminar ni winsorizar outliers automáticamente;
4. identificar variables deterministas/redundantes y probarlas por ablation;
5. tratar Availability como estado as-of **más una medida de staleness**;
6. tratar Market Context como panel con cobertura/publicación explícita;
7. bloquear current-state Spot fields en scoring histórico;
8. no asumir que ratios de fit cercanos a 1 son mejores en este proxy;
9. construir cualquier perfil de broker sólo con historia previa y shrinkage;
10. validar separadamente la semántica de `prior_searches` y `prior_inquiries`.
