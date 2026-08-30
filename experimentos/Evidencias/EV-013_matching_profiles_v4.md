# EV-013 — Semantic profiles + Dynamic Need + Broker Service + hierarchical matching

**Estado:** empírica completa; incluye resultados positivos, negativos y gates de representación.

## Experimentos

- [E008 Behavioral Persona](../matching_profiles_v4/specs/E008_behavioral_persona.json)
- [E009 Dynamic Need T1](../matching_profiles_v4/specs/E009_dynamic_need_t1.json)
- [E010 Clean Broker Profiles](../matching_profiles_v4/specs/E010_clean_broker_profiles.json)
- [E011 Hierarchical Matching](../matching_profiles_v4/specs/E011_hierarchical_matching.json)
- [E012 Dynamic Need Strong Baseline](../matching_profiles_v4/specs/E012_dynamic_need_strong_baseline.json)
- [E013 Balanced Broker Profiles](../matching_profiles_v4/specs/E013_balanced_broker_profiles.json)
- [E014 Hierarchical Matching v2](../matching_profiles_v4/specs/E014_hierarchical_matching_v2.json)
- [E015 Broker Service](../matching_profiles_v4/specs/E015_broker_service_profile.json)
- [E016 Dynamic + Service Hierarchy](../matching_profiles_v4/specs/E016_dynamic_service_hierarchy.json)
- [Interpretabilidad completa](../matching_profiles_v4/INTERPRETABILIDAD.md)

## Trazabilidad autoritativa

- Matching profiles v4: [run 33287168139](https://github.com/jcval94/spot2/actions/runs/33287168139) — **success**.
- Governance CI: [run 33287168148](https://github.com/jcval94/spot2/actions/runs/33287168148) — **success**.
- Commit reproducible de resultados: [969c953](https://github.com/jcval94/spot2/commit/969c953245a501310d676af3060c4c9f6c91d71b).
- Future test: 4,516 inquiries / 2,065 Leads, idéntico a EV-010.
- Baseline scheduled_visit inquiry-level ≈20.77%.
- Clustering outcome-free; bootstrap por `lead_id`.

## 1. Persona: semántica mejor, scoring peor

Behavioral Persona:
- GMM K=3.
- min 14.8%, max 59.0%.
- ARI 1.000.

Perfiles:
- BP1 baja historia.
- BP2 manufacturing/baja historia.
- BP3 alta madurez, 85% conversión previa y prior inquiries altas.

E008 vs E006:
- AP 0.20981 → 0.20268.
- ΔAP -0.00711, IC95% [-0.01497,+0.00044], P(Δ>0)=3.5%.
- Lift@10 1.001x → 0.937x.

**Resultado:** no soportado como reemplazo predictivo; sí más interpretable.

## 2. Dynamic Need

K-Means K=5:
- silhouette **0.620**.
- ARI **1.000**.
- min 5.29%, max 64.99%.
- weekday excluido.

E012, aislado directamente sobre E006:
- AP 0.21135 vs 0.20981.
- Lift@10 **1.108x vs 1.001x**.
- Recall@20 **21.96% vs 19.72%**.
- ΔAP +0.00131, IC95% [-0.00690,+0.00881].
- ΔLift@10 +0.0995, IC95% [-0.0753,+0.2735].
- ΔRecall@20 +0.0211, IC95% [-0.00003,+0.04158], P(Δ>0)=97.25%.

**Resultado:** señal direccional útil pero todavía INCONCLUSIVE para mejora global.

La transición T0→T1 es asimétrica:
- N1→DN1 99.82%.
- N2 y N3 se reparten ampliamente entre DN1–DN5.

## 3. Broker Supply: dos intentos fallan

Primer intento:
- 98.3% / 1.3% / 0.3%.

Segundo intento compacto/winsorizado:
- BSP1 70.3%.
- BSP2 26.0%.
- BSP3 3.7%.
- ARI 0.949.
- gate requerido: min>=5%, max<=65%.
- **FAIL**.

E013 queda **NOT_SUPPORTED** por representation gate; sus métricas se copian intencionalmente del padre sólo para registrar el harness, no representan un tratamiento ejecutado.

E014 también queda **NOT_SUPPORTED/no elegible** porque dependía de E013.

## 4. Broker Service sí produce una segmentación defendible

Broker Service balanced:
- Bisecting K=3.
- min 18.7%, max 57.7%.
- ARI **0.948**.

Perfiles:
- BSV1 servicio diversificado/mayor actividad.
- BSV2 acceptance-heavy/menor volumen.
- BSV3 mayor urgencia y scheduled_visit histórico.

E015 vs E012:
- AP 0.211347 → 0.211344.
- ΔAP -0.00002, IC95% [-0.00062,+0.00059].
- Lift@10 1.108x → 1.118x.

**Resultado:** válido como segmentación, INCONCLUSIVE como mejora predictiva marginal.

## 5. Jerarquía Dynamic Need + Broker Service

E016:
- AP 0.21068.
- Lift@10 **1.172x**.
- lead-level AP 0.4049.
- lead-level AUC 0.5730.
- lead Lift@10 1.365x.

Vs E015:
- ΔAP +0.00005, IC95% [-0.01072,+0.01108].
- ΔLift@10 +0.0499, IC95% [-0.1548,+0.2474].
- AUC baja puntualmente.

Vs old E007:
- ΔAP -0.00097, IC95% [-0.01650,+0.01471].
- ΔLift@10 +0.1374, IC95% [-0.0914,+0.3697].

**Resultado:** INCONCLUSIVE. Mejora concentración top-decile en punto, pero no sustituye robustamente a E007.

## 6. No hay nuevo ganador global

| Modelo | AP | Lift@10 | Lead AP | Lead AUC |
|---|---:|---:|---:|---:|
| E006 | 0.20981 | 1.001x | 0.3752 | 0.5469 |
| E012 | 0.21135 | **1.108x** | 0.3801 | 0.5584 |
| E015 | 0.21134 | **1.118x** | 0.3809 | 0.5595 |
| E016 | 0.21068 | **1.172x** | 0.4049 | 0.5730 |
| E007 old | **0.21171** | 1.033x | **0.4270** | **0.5899** |

La optimización depende de objetivo:
- E007 mantiene mejor AP/global Lead ranking.
- E012/E015/E016 aumentan lift@10 puntual.
- ningún delta relevante separa robustamente a los candidatos bajo bootstrap.

## 7. Nuevo récord local

### DN4 × LOC1 × BSV1

- N=60.
- raw scheduled_visit: **36.67%**.
- tasa suavizada: **31.37%**.
- lift: **1.510x**.
- Wilson lower rate / baseline: **1.234x**.

Es el mayor lift local registrado hasta ahora.

Otras celdas:
- N3→DN4 × BSV1: N=83, **1.373x**, Wilson lower lift 1.077x.
- N2→DN2 × BSV3: N=57, 1.341x.
- DN4 × LOC1: N=90, 1.333x.
- PH3 × BSV2: N=159, 1.305x.
- DN4 × BSV1: N=153, 1.295x.

**Cautela:** las celdas se inspeccionaron en future test y hay múltiples comparaciones. Son hipótesis de routing, no confirmación independiente.

## 8. Evidencia fuente

- [README](../matching_profiles_v4/README.md)
- [model_metrics.csv](../matching_profiles_v4/results/model_metrics.csv)
- [bootstrap_deltas.csv](../matching_profiles_v4/results/bootstrap_deltas.csv)
- [selected_clusterers.csv](../matching_profiles_v4/results/selected_clusterers.csv)
- [profile_interpretability.csv](../matching_profiles_v4/results/profile_interpretability.csv)
- [need_t0_t1_transition_matrix.csv](../matching_profiles_v4/results/need_t0_t1_transition_matrix.csv)
- [broker_supply_balance_gate.json](../matching_profiles_v4/results/broker_supply_balance_gate.json)
- [broker_service_balance_gate.json](../matching_profiles_v4/results/broker_service_balance_gate.json)
- [top_service_compatibility_cells.csv](../matching_profiles_v4/results/top_service_compatibility_cells.csv)
- [E012 results](../matching_profiles_v4/results/E012_dynamic_need_strong_baseline_results.json)
- [E013 results](../matching_profiles_v4/results/E013_balanced_broker_profiles_results.json)
- [E015 results](../matching_profiles_v4/results/E015_broker_service_profile_results.json)
- [E016 results](../matching_profiles_v4/results/E016_dynamic_service_hierarchy_results.json)

## 9. Descubrimientos relacionados

[D038–D049](../conocimiento_agregado/DESCUBRIMIENTOS.md)
