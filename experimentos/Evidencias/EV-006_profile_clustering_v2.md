# EV-006 — Profile clustering benchmark v2

**Estado de evidencia:** empírica, selección no supervisada outcome-free + perfiles congelados + future test.

**Experimento:** [profile_clustering_v2](../profile_clustering_v2/)

## Trazabilidad de ejecución

- GitHub Actions: [run 33276365674](https://github.com/jcval94/spot2/actions/runs/33276365674) — success.
- Commit de resultados reproducibles: [35bfd6f](https://github.com/jcval94/spot2/commit/35bfd6ff80347f95b76653a76ba57e3c90d57ce5).
- Profile cutoff: 2025-09-29T12:58:37.
- Test cutoff: 2026-04-28T07:41:43.
- Calibración de perfiles: 6,772 inquiries (primer 30% temporal).
- Train predictivo: 11,288 inquiries.
- Future test: 4,516 inquiries (20% final).
- Tasa future de scheduled_visit: 20.8%.

## Evidencia fuente

- [README / reporte](../profile_clustering_v2/README.md)
- [Summary JSON](../profile_clustering_v2/results/summary.json)
- [Benchmark completo de clustering](../profile_clustering_v2/results/clustering_benchmark.csv)
- [Clusterers seleccionados](../profile_clustering_v2/results/selected_clusterers.csv)
- [Interpretabilidad por cluster](../profile_clustering_v2/results/profile_interpretability.csv)
- [Métricas E001/E002/E003](../profile_clustering_v2/results/model_metrics.csv)
- [Bootstrap de deltas](../profile_clustering_v2/results/bootstrap_deltas.csv)
- [Top Lead × Spot × Broker](../profile_clustering_v2/results/top_3entity_combinations.csv)
- [Search Need × Spot](../profile_clustering_v2/results/need_spot_performance.csv)
- [Inquiry Intent × Search Need](../profile_clustering_v2/results/intent_need_performance.csv)
- [Inquiry Intent × Spot](../profile_clustering_v2/results/intent_spot_performance.csv)
- [Inquiry Intent × Broker](../profile_clustering_v2/results/intent_broker_performance.csv)
- [Revisión de entidades/facetas](../profile_clustering_v2/results/entity_profile_review.csv)
- [E001 results](../profile_clustering_v2/results/E001_balanced_profiles_results.json)
- [E002 results](../profile_clustering_v2/results/E002_lead_facets_results.json)
- [E003 results](../profile_clustering_v2/results/E003_inquiry_intent_results.json)

## 1. Calidad de clustering

La selección comparó K-Means, Bisecting K-Means, BIRCH y Gaussian Mixture para K=3…7 **sin usar el outcome**. El criterio de balance exige cluster mínimo >=5% y máximo <=70%.

| Familia | Método | K | Mínimo | Máximo | ARI estabilidad |
|---|---|---:|---:|---:|---:|
| Lead | K-Means | 6 | 7.5% | 43.7% | 0.659 |
| Lead Persona | K-Means | 3 | 11.2% | 51.4% | 0.999 |
| Search Need | K-Means | 3 | 23.7% | 46.3% | 1.000 |
| Spot | Bisecting K-Means | 7 | 9.5% | 27.3% | 0.410 |
| Broker | Bisecting K-Means | 7 | 7.0% | 22.0% | 0.443 |
| Inquiry Intent | Gaussian Mixture | 7 | 6.5% | 26.0% | 0.737 |

**Resultado:** el problema de clusters dominantes cercanos a 90% queda corregido en todas las familias seleccionadas.

## 2. Señal predictiva fuera de muestra

| Modelo | ROC AUC | AP | Brier | Log-loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| Global baseline | 0.500 | 0.208 | 0.165 | 0.511 | 1.000x | 20.0% |
| E001 balanced profiles | 0.513 | 0.212 | 0.166 | 0.515 | 1.033x | 20.8% |
| E002 Lead Persona + Search Need | 0.513 | 0.215 | 0.167 | 0.519 | 1.023x | 21.7% |
| E003 + Inquiry Intent | 0.491 | 0.203 | 0.167 | 0.520 | 0.905x | 19.6% |

Bootstrap:

- E002 vs E001: ΔAUC +0.0005, IC95% [-0.0257, +0.0257]; ΔAP +0.0028, IC95% [-0.0134, +0.0185].
- E003 vs E002: ΔAUC -0.0200, IC95% [-0.0442, +0.0018]; ΔAP -0.0106, IC95% [-0.0261, +0.0036]; ΔLift@10% -0.142, IC95% [-0.361, +0.080].

**Resultado:** E002 es el mejor por AP, pero no existe evidencia robusta de lift incremental frente a E001. E003 no está soportado.

## 3. Interpretabilidad material

### Lead Persona vs Search Need

- Persona P1: tenant_direct dominante.
- Persona P2: broker dominante.
- Persona P3: mayor historial de búsquedas.
- Need N1: renta dominante.
- Need N2: venta dominante.
- Need N3: modalidad both y mayor área.

La separación produce perfiles más comprensibles y muy estables, pero no prueba mejora predictiva material.

### Inquiry Intent

La solución GMM es balanceada, pero I1–I6 quedan dominados principalmente por weekday; I7 se distingue por área y presupuestos solicitados altos.

**Resultado:** la versión actual captura calendario más que intención comercial accionable.

### Spot

Varios perfiles quedan dominados por geografía:

- S2 CDMX/centro.
- S3 Bajío/Querétaro.
- S5 Nuevo León.
- S6 Estado de México.
- S7 Jalisco.
- S4 es más físico (piso/elevadores).

**Resultado:** Spot mezcla “qué inmueble es” con “dónde está”.

## 4. Compatibilidades locales

Celdas futuras con soporte y lift descriptivo relevante:

| Combinación | N | Scheduled visit | Lift |
|---|---:|---:|---:|
| L1 × S1 × B5 | 93 | 30.1% | 1.31x |
| N2 × S3 | 197 | 25.4% | 1.18x |
| N1 × S5 | 157 | 24.8% | 1.16x |
| N1 × S6 | 172 | 24.4% | 1.14x |

Estas celdas son hipótesis útiles de routing/matching, no una prueba de sinergia causal o generalizable.

## 5. Alcance recomendado de perfiles

| Componente | Decisión |
|---|---|
| Lead Persona | Perfilar |
| Search Need | Perfilar |
| Spot | Perfilar, pero separar después físico vs localización |
| Broker | Perfilar |
| Inquiry Intent | Sólo T1; versión actual NOT_SUPPORTED |
| Spot Attributes | Integrar en Spot; relación 1:1 |
| Availability Snapshot | Usar como estado temporal directo, no clusterizar |
| Geography | Dimensión de matching/contexto, no entidad conductual |
| Market Context | Contexto/régimen potencial; no usar históricamente sin semántica de publicación as-of |

## Validación y leakage

- Los clusterers se aprenden sólo en la ventana temprana de calibración.
- Los perfiles de broker usan únicamente spots/inquiries anteriores al profile cutoff y se congelan antes del train predictivo.
- lead_score_internal, days_on_market, total_inquiries, total_views e is_active no entran en los perfiles.
- broker_response define el proxy target; broker_response_hours sólo entra en historia previa del broker.
- Inquiry Intent usa únicamente información disponible en inquiry_at.
- scheduled_visit es un proxy de avance comercial, no venta/cierre real.

## Qué demuestra / qué no demuestra

**Demuestra:**

- que se pueden construir perfiles no degenerados y explicables;
- que Persona y Search Need son facetas semánticamente útiles;
- que Inquiry Intent v1 no mejora la priorización futura;
- que el Spot actual mezcla geografía con arquetipo físico;
- que existen celdas locales de matching dignas de validación adicional.

**No demuestra:**

- causalidad;
- lift material de un Compatibility Score global;
- que cada celda local se mantenga estable en producción;
- que scheduled_visit equivalga a venta real.

## Descubrimientos relacionados

- [D006 — Clustering balanceado mejora perfiles, no prueba lift material](../conocimiento_agregado/DESCUBRIMIENTOS.md#d006--clustering-balanceado-mejora-perfiles-no-prueba-lift-material)
- [D009 — Persona y necesidad deben tratarse como facetas distintas](../conocimiento_agregado/DESCUBRIMIENTOS.md#d009--persona-y-necesidad-deben-tratarse-como-facetas-distintas)
- [D010 — Inquiry Intent v1 aprende calendario, no intención útil](../conocimiento_agregado/DESCUBRIMIENTOS.md#d010--inquiry-intent-v1-aprende-calendario-no-intención-útil)
- [D011 — Spot mezcla qué es con dónde está](../conocimiento_agregado/DESCUBRIMIENTOS.md#d011--spot-mezcla-qué-es-con-dónde-está)
- [D012 — Compatibilidades locales sin química global demostrada](../conocimiento_agregado/DESCUBRIMIENTOS.md#d012--hay-compatibilidades-locales-pero-no-una-química-global-demostrada)
