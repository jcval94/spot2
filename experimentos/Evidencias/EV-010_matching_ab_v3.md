# EV-010 — Relational audit + Matching A/B v3

**Estado de evidencia:** empírica completa + diseño online pre-registrado.

- [E006 — Physical vs Location Spot](../matching_ab_v3/specs/E006_physical_location_spot.json)
- [E007 — Compatibility Routing](../matching_ab_v3/specs/E007_compatibility_routing.json)
- [README](../matching_ab_v3/README.md)
- [Interpretabilidad completa](../matching_ab_v3/INTERPRETABILIDAD.md)

## Trazabilidad autoritativa

- Matching A/B v3: [run 33281634395](https://github.com/jcval94/spot2/actions/runs/33281634395) — **success**.
- Governance CI: [run 33281634393](https://github.com/jcval94/spot2/actions/runs/33281634393) — **success**.
- Commit reproducible: [9be9e43](https://github.com/jcval94/spot2/commit/9be9e4350dc38e6777e8cbde60a904c4765bb82a).
- Profile cutoff: 2025-09-29T12:58:37.
- Future-test cutoff: 2026-04-28T07:41:43.
- Future test: 4,516 inquiries / 2,065 leads.
- Future scheduled_visit: 20.77% inquiry-level; 34.33% lead-level.

## 1. Auditoría relacional

0 fallos CRITICAL. PK/FK, cardinalidades, joins y temporalidad pasaron.

Un join directo Inquiry×Availability por `spot_id` expande filas **10.02x**. El pipeline correcto usa `latest snapshot_date <= inquiry_at`:

- coverage global: 92.38%;
- coverage lag<=90d: 88.51%;
- snapshots futuros usados: 0.

Availability es internamente consistente, pero su coverage es temporalmente no estacionario: 6.5% en ene-2025, 84.7% en jun-2025, 96.6% en sep-2025 y 100% desde ene-2026.

## 2. Cross-table Lead → Inquiry → Spot

- modalidad compatible: **100.0%**;
- sector exacto: **70.35%**;
- municipio preferido exacto: **19.80%**;
- corredor exacto cuando se declara: **18.60%**.

La inquiry refina la necesidad:

- requested rent budget dentro del rango inicial: **81.53%**;
- requested sale budget dentro del rango inicial: **81.04%**;
- mediana requested_area / target_area: **1.053x**;
- requested area dentro de 0.5x–2x del target: **62.16%**.

## 3. Completitud y consistencia

Condicionado a modalidad:

- Lead min rent 96.64%, max rent 100%.
- Lead min sale 96.40%, max sale 100%.
- Spot rent/sale prices 100%.

0 casos min_budget > max_budget.

`price_total ≈ price_sqm × area` está dentro de 1% para **100%** de los listings comparables de renta y venta.

## 4. Campos con semántica problemática

### broker_response_hours

- 3,786 `no_response` tienen response_hours.
- 2,701 outcomes de respuesta no tienen response_hours.
- non-null rate ~85% en todos los outcomes.
- medianas ~8.1–8.5h en todos los outcomes.

No debe interpretarse directamente como SLA limpio.

### spots.total_inquiries

Contra el conteo real de `inquiries` por spot:

- exact match 7.07%;
- total_inquiries >= event count 37.43%;
- correlación -0.051;
- diferencia mediana -2.

No equivale al historial de eventos candidate.

## 5. Market Context

Coverage exacta Spot geography × sector × inquiry month:

- global **23.84%**;
- Industrial 26.76%;
- Land 19.73%;
- Office 22.34%;
- Retail 24.95%;
- julio-2026 0%.

Sin effective/publication time no es una feature histórica point-in-time defendible.

## 6. E006 — Physical Space vs Location

| Modelo | AUC | AP | Lift@10% | Lead AP | Lead AUC |
|---|---:|---:|---:|---:|---:|
| A Unified Spot | 0.5000 | 0.2100 | 1.023x | 0.3728 | 0.5441 |
| B Physical + Location | 0.4985 | 0.2098 | 1.001x | 0.3752 | 0.5469 |

ΔAP B−A **-0.00005**, IC95% **[-0.00572, +0.00550]**.

**Conclusión: INCONCLUSIVE.** Mejora interpretabilidad, no lift demostrado.

Physical: GMM K=4, min 6.6%, max 51.1%, ARI 0.689.  
Location: K-Means K=7, min 5.9%, max 33.4%, ARI **1.000**.

## 7. E007 — Compatibility Routing

| Modelo | AUC | AP | Lift@10% | Recall@20% | Lead AP | Lead AUC |
|---|---:|---:|---:|---:|---:|---:|
| A Marginals | 0.4985 | 0.2098 | 1.001x | 19.72% | 0.3752 | 0.5469 |
| B Interactions | 0.4985 | 0.2117 | 1.033x | 20.68% | **0.4270** | **0.5899** |

ΔAP **+0.00205**, IC95% **[-0.00960, +0.01294]**.

**Conclusión: INCONCLUSIVE.** Hay señal lead-level y local, pero no evidencia robusta para un Compatibility Score global.

## 8. Mejores celdas future-test

N>=50 y shrinkage al baseline.

| Combinación | N | Visit rate | Smooth | Lift |
|---|---:|---:|---:|---:|
| N2 × PH1 × B6 | 73 | 31.5% | 28.38% | **1.37x** |
| N3 × PH1 × B5 | 81 | 29.6% | 27.24% | **1.31x** |
| N3 × LOC6 | 64 | 29.7% | 26.84% | **1.29x** |
| PH3 × B2 | 99 | 28.3% | 26.54% | **1.28x** |
| PH3 × B1 | 139 | 27.3% | 26.17% | **1.26x** |
| N2 × PH2 × B3 | 67 | 28.4% | 26.01% | **1.25x** |
| PH2 × B3 | 184 | 25.5% | 24.87% | **1.20x** |
| N2 × LOC2 | 258 | 24.8% | 24.39% | **1.17x** |
| N1 × PH2 × B3 | 78 | 25.6% | 24.29% | **1.17x** |
| N3 × B5 | 132 | 25.0% | 24.22% | **1.17x** |

La interpretación cluster por cluster y de cada combinación está en [INTERPRETABILIDAD.md](../matching_ab_v3/INTERPRETABILIDAD.md).

## 9. A/B online pre-registrado

- unidad: `lead_id`;
- 50/50 sticky;
- estratificación sector × modalidad × user_type;
- primary outcome: al menos una scheduled_visit por Lead en 30 días;
- ITT, horizonte fijo, alpha 0.05, IC95%, sin optional stopping;
- guardrails: SRM, eligibility, availability coverage/lag, unavailable recommendations, broker workload concentration, no-result rate.

Power con baseline 34.33%:

| MDE | N/arm | N total |
|---:|---:|---:|
| 1 pp | 35,633 | 71,266 |
| 1.5 pp | 15,889 | 31,778 |
| 2 pp | 8,966 | 17,932 |
| 2.5 pp | 5,756 | 11,512 |
| 3 pp | 4,010 | 8,019 |

El future test actual tiene 2,065 Leads: no está potenciado para resolver efectos pequeños.

## 10. Evidencia fuente

- [relationship_checks.csv](../matching_ab_v3/results/relationship_checks.csv)
- [content_consistency_checks.csv](../matching_ab_v3/results/content_consistency_checks.csv)
- [response_hours_by_response.csv](../matching_ab_v3/results/response_hours_by_response.csv)
- [lead_spot_match_by_search_sector.csv](../matching_ab_v3/results/lead_spot_match_by_search_sector.csv)
- [lead_inquiry_need_consistency.csv](../matching_ab_v3/results/lead_inquiry_need_consistency.csv)
- [spot_price_arithmetic_consistency.csv](../matching_ab_v3/results/spot_price_arithmetic_consistency.csv)
- [spot_total_inquiries_vs_event_table_summary.csv](../matching_ab_v3/results/spot_total_inquiries_vs_event_table_summary.csv)
- [availability_coverage_by_month.csv](../matching_ab_v3/results/availability_coverage_by_month.csv)
- [availability_state_consistency.csv](../matching_ab_v3/results/availability_state_consistency.csv)
- [market_context_coverage_by_sector.csv](../matching_ab_v3/results/market_context_coverage_by_sector.csv)
- [market_context_coverage_by_month.csv](../matching_ab_v3/results/market_context_coverage_by_month.csv)
- [spot_decomposition_interpretability.csv](../matching_ab_v3/results/spot_decomposition_interpretability.csv)
- [model_metrics.csv](../matching_ab_v3/results/model_metrics.csv)
- [bootstrap_deltas.csv](../matching_ab_v3/results/bootstrap_deltas.csv)
- [compatibility_cells_future_test.csv](../matching_ab_v3/results/compatibility_cells_future_test.csv)
- [online_ab_protocols.json](../matching_ab_v3/results/online_ab_protocols.json)
- [power_analysis.csv](../matching_ab_v3/results/power_analysis.csv)

## 11. Descubrimientos relacionados

D023–D033 en [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
