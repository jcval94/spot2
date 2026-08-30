# EV-020 — EDA profundo: drift, outliers y temporalidad

**Estado de evidencia:** empírica, descriptiva + detección no supervisada outcome-free.

**Experimento:** [E020 — eda_profundo](../eda_profundo/)

## Pregunta

¿Qué propiedades distribucionales, temporales y de generación de los datos pueden inducir conclusiones erróneas antes del feature engineering del sistema dinámico T0/T1/T2?

## Por qué este EDA es parte de la evaluación

Un feature puede ser point-in-time correcto y aun así no ser estable. El caso más importante aquí es el tiempo: si la mecánica de generación cambia por cohorte, un modelo puede aprender “en qué periodo estoy” en lugar de una relación comercial reutilizable. Por eso esta evidencia separa:

- leakage: información futura;
- drift: cambio del proceso/distribución;
- current-state inconsistente: variable que no puede reconstruirse históricamente;
- rareza/outlier: observación infrecuente pero no necesariamente errónea;
- artefacto sintético: regla de generación visible en las distribuciones.

## Resultados que motivan follow-ups

### Drift temporal

El total de inquiries por lead permanece aproximadamente en 4.2–4.8, pero las inquiries dentro de los primeros 30 días pasan de **1.37 por lead en 2025-01** a **4.42 en 2026-06**.

La mediana de tiempo a primera inquiry cae de **7.82** a **2.31 días**. En paralelo, el proxy lead-level a 30 días pasa de ~20.1% a ~56.5%.

**Por qué importa:** el horizonte del target es fijo (30 días). Si el generador comprime las interacciones hacia el alta del lead, aumenta mecánicamente la oportunidad de observar eventos dentro de ese horizonte. Variables como `days_from_lead_creation`, `inquiry_number`, `days_since_first_inquiry` o calendario pueden capturar esa transición de régimen.

**Qué no demuestra:** que responder/interactuar antes cause una visita; tampoco demuestra leakage.

**Experimentos derivados:** E021 rolling drift stress y E022 temporal-feature ablation.

### Clipping y redundancias sintéticas

- `requested_area / spot_area ≈ 0.30`: **35.53%**.
- `requested_area / spot_area ≈ 5.00`: **21.37%**.
- requested rent exactamente igual al máximo del lead: **25.16%**.
- requested sale exactamente igual al máximo del lead: **24.75%**.
- `spot price_total ≈ area × price_sqm`: error relativo p99 **5.05e-7** renta, **2.83e-9** venta.

**Por qué importa:** varias columnas no representan grados de libertad independientes. Un modelo puede repartir importancia entre copias algebraicas de la misma señal y volver frágil la interpretación.

**Experimento derivado:** E025 redundancy ablation.

### Outliers

Isolation Forest outcome-free, por sector × modalidad:

- 155 lead flags;
- 94 spot flags;
- 685 inquiry flags.

Los flags tienen mucha mayor presencia de extremos univariados que los no flags, pero la rareza no mejora el proxy. En inquiries: top 1% más anómalo ~17.95% scheduled_visit vs ~19.94% en el resto; top 3% ~19.12% vs ~19.94%.

**Por qué importa:** existe rareza multivariable real, pero no evidencia de que sea error ni oportunidad. Eliminar filas por rareza puede borrar regímenes válidos.

**Experimento derivado:** E024, donde el detector se ajusta sólo con train y validation/test permanecen intactos.

### Availability y staleness

- ~90.27% de spots cambia availability al menos una vez.
- mediana ~4 transiciones y ~10 snapshots.
- gap entre snapshots: mediana **21 días**, p95 **97**, p99 **155**, máximo **319**.

**Por qué importa:** un backward as-of join evita leakage, pero un snapshot viejo puede ser legal y a la vez poco confiable. `availability_snapshot_age_days` puede además funcionar como proxy de periodo/cobertura.

**Experimento derivado:** E023 staleness guardrail.

### Current-state Spot

Con fin observable 2026-07-13:

- 373 spots (**12.43%**) tienen `days_on_market` mayor que el tiempo transcurrido desde `created_at`;
- 17 implican >365 días futuros;
- p99 del desfase: +308 días;
- máximo: +694 días;
- `spots.total_inquiries` coincide exactamente con inquiries observables sólo en **7.07%** de los spots.

**Por qué importa:** esos campos no forman snapshots históricos coherentes.

**Decisión:** siguen BLOCK para scoring histórico salvo reconstrucción point-in-time demostrable.

### prior_searches vs prior_inquiries

Correlación Pearson: **-0.00495**.

**Por qué importa:** correlación casi cero no significa que una sea inútil ni que deban sumarse. Puede indicar dos procesos distintos.

**Experimento derivado:** E026, ablación separada y conjunta.

### Broker

Con al menos 50 inquiries, scheduled_visit descriptivo varía aproximadamente **9.86%–32.79%**.

**Por qué importa:** hay heterogeneidad suficiente para preguntar si existe señal histórica del broker.

**Qué no demuestra:** efecto causal del broker; cartera, geografía, Spot mix, lead mix y tiempo confunden la tasa.

**Experimento derivado:** E027, prior histórico suavizado estrictamente point-in-time, sin broker_id como identidad.

### Market Context

72 claves geo-sector, 30 meses globales, sólo 3–12 meses por clave, mediana 7 y 0 claves completas.

**Decisión:** no se promueve a feature predictiva en esta batería. Sin semántica de publicación/as-of, el experimento no sería defendible.

## Evidencia fuente

- [Hallazgos completos](../eda_profundo/FINDINGS.md)
- [Metodología](../eda_profundo/README.md)
- [Runner reproducible](../eda_profundo/run_deep_eda.py)
- `eda_profundo/results/`
- `eda_profundo/figures/` — 20 diagnósticos visuales.
- `eda_profundo/base_eda/` — EDA previo migrado.

## Leakage / límites

- hidden outcomes no usados;
- `lead_score_internal` excluido del espacio de anomalías;
- respuestas actuales/futuras del broker excluidas de Inquiry anomalies;
- current-state Spot fields excluidos del espacio de anomalías;
- Availability se estudia como trayectoria as-of;
- scheduled_visit se mira sólo después del fit del detector para diagnóstico descriptivo.

## Descubrimientos

D060–D068 en [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
