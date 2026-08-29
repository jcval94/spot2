# EDA profundo — hallazgos

## Resumen

Este análisis profundiza el EDA base sin entrenar el Modelo 3. La conclusión central es que **el dataset no debe tratarse como una tabla IID con outliers removibles**: contiene colas por régimen, paneles temporales incompletos y varias restricciones sintéticas del generador.

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

## 2. Hay clipping explícito en la construcción de inquiries

### Área solicitada vs Spot

`requested_area_sqm / spot.area_sqm` tiene:

- ~35.5% de masa cerca de **0.30**;
- ~21.4% cerca de **5.00**;
- mínimo ~0.30 y máximo 5.00.

Esto es una firma muy clara de clipping.

### Presupuesto solicitado vs presupuesto máximo del lead

- Rent: ~25.1% de los casos con ambos valores son exactamente 100% del máximo del lead.
- Sale: ~24.7% son exactamente 100%.
- Prácticamente toda la masa está entre ~70% y 100%.

**Lectura:** estas variables contienen intención, pero también una regla del generador. No deben interpretarse como señales independientes puramente orgánicas.

## 3. Precio total del Spot es casi redundante

En los registros con valores disponibles:

`price_total ≈ area_sqm × price_sqm`

El p99 del error relativo es aproximadamente:

- renta: **5.0e-7**;
- venta: **2.8e-9**.

**Implicación posterior:** usar simultáneamente área, precio/m² y precio total puede introducir redundancia casi determinista. Esto no es todavía una decisión de feature selection, pero sí una advertencia.

## 4. Las distribuciones tienen colas fuertes y múltiples escalas

Ejemplos:

- Lead target area: mediana 393 m², p95 1,479, p99 7,665, máximo 9,962.
- Inquiry requested area: mediana 484 m², p95 4,898, p99 12,774, máximo 40,921.
- Spot area: mediana 617 m², p95 15,562, p99 42,221, máximo 136,403.
- Spot sale total: mediana ~19.8 M MXN, p99 ~677.6 M, máximo ~1.88 B.
- Maintenance: mediana ~10.4k, p99 ~379k, máximo ~1.67 M.
- Lead prior inquiries: mediana 1, p95 78, p99 145, máximo 199.

Para muchas variables el criterio Tukey marca 7–13% como outliers, demasiado para asumir que son “errores raros”.

## 5. Isolation Forest: resultado diagnóstico

Se aplicó conceptualmente por régimen sector × modalidad y sin leakage:

- Lead: T0-safe.
- Spot: sólo atributos estáticos.
- Inquiry: sólo contenido conocido en `inquiry_at`.
- contamination: 3%.

En la ejecución diagnóstica:

- Leads marcados: ~3% por régimen; **80.1%** de esos flags también tienen algún extremo univariado.
- Spots: **98.9%** de flags también tienen algún extremo univariado.
- Inquiries: **64.7%** de flags también tienen algún extremo univariado.

La tasa de `scheduled_visit` en inquiries marcadas fue **19.1%**, frente a **19.9%** en las no marcadas.

**Lectura:** el bosque detecta sobre todo combinaciones de escala inusuales; no descubre una población oculta de oportunidades ni justifica eliminar filas.

Casos extremos de Spot incluyen combinaciones como áreas >100k m², cientos/miles de estacionamientos, pisos muy altos o muchos elevadores dentro de regímenes donde eso es infrecuente. Son candidatos a inspección, no errores demostrados.

## 6. Historial previo parece una mezcla de poblaciones

- `prior_searches`: 34.5% es cero; mediana 2; p95 44; máximo 60.
- `prior_inquiries`: 44.4% es cero; mediana 1; p95 78; máximo 199.
- La correlación entre ambas es prácticamente **0** (~-0.005).

Es llamativo porque semánticamente parecen relacionadas. Puede indicar que representan procesos distintos o que fueron generadas de forma casi independiente.

## 7. Availability es profundamente temporal

Sobre 3,000 spots:

- mediana: 10 snapshots;
- ~90.3% cambia de estado al menos una vez;
- mediana: 4 transiciones;
- sólo ~6.8% permanece siempre disponible;
- ~2.9% siempre no disponible.

Cuando no está disponible, `days_until_available` tiene mediana ~41 días, p95 ~176 y máximo 671.

**Lectura:** Availability no debe convertirse en una propiedad permanente de Spot ni entrar a un detector de anomalías cross-sectional global.

## 8. Market Context es un panel rotatorio/incompleto

- 72 claves geo-sector.
- 30 meses distintos globalmente.
- cada clave aparece sólo 3–12 meses;
- mediana 7 meses;
- **0 claves** cubren los 30 meses.

Esto explica la cobertura exacta ~23% del EDA base. Un forward-fill indiscriminado crearía información difícil de defender point-in-time.

## 9. Correlaciones que llaman la atención

- Spot `total_views` vs `total_inquiries`: **0.904**.
- log(area) vs log(rent total): **0.918**.
- log(area) vs log(sale total): **0.913**.
- days_on_market vs total_views: **0.670**.
- Market occupancy vs absorption days: **-0.448**.
- Market occupancy vs avg price/m²: **0.512**.
- Lead log(target area) vs log(max budget): ~0.60–0.63.

Las primeras correlaciones refuerzan que varios campos de Spot son agregados/derivados o estado actual, no fuentes independientes históricas.

## 10. La compatibilidad intuitiva apenas mueve scheduled_visit

En crudo:

- mismo estado: ~20.7% vs 19.6%;
- mismo municipio: ~20.9% vs 19.7%;
- mismo corredor: ~20.8% vs 19.7%.

Y los buckets de budget/spot price o requested area/spot area permanecen relativamente planos. De hecho, el bucket de presupuesto cercano a 1 no es el mejor.

**Lectura:** este proxy sintético está débilmente acoplado a una noción simple de economic/geographic fit. Esto ayuda a explicar el lift limitado de los experimentos globales de matching.

## 11. Existe heterogeneidad descriptiva de broker con soporte

Entre brokers con >=50 inquiries se observan tasas aproximadas desde **9.9%** hasta **32.8%**.

Eso es una dispersión material, pero puede mezclar:

- cartera;
- geografía;
- tipo de spot;
- lead mix;
- tiempo.

**Implicación:** merece experimentarse con perfiles históricos point-in-time y shrinkage, no con una tasa full-dataset interpretada como “calidad causal del broker”.

## Conclusión para el siguiente paso

El feature engineering debería partir de estas reglas, sin implementarlas todavía aquí:

1. preservar tiempo/cohorte explícitamente;
2. preferir representaciones robust/log para variables de escala;
3. no eliminar outliers automáticamente;
4. identificar variables deterministas/redundantes;
5. tratar Availability como estado as-of;
6. tratar Market Context como panel con cobertura/publicación explícita;
7. no asumir que ratios de fit cercanos a 1 son necesariamente mejores en este proxy;
8. construir cualquier perfil de broker sólo con historia previa.
