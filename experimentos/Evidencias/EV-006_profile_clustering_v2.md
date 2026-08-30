# EV-006 — Profile clustering benchmark v2

**Estado de evidencia:** empírica; esta versión refleja el **rerun autoritativo actual**.

## Trazabilidad

- [GitHub Actions run 33278286046](https://github.com/jcval94/spot2/actions/runs/33278286046) — success.
- Commit actual: [c32f54a](https://github.com/jcval94/spot2/commit/c32f54a0d41757d1e56a76e19ef362ca4bb1877e).
- Profile cutoff: 2025-09-29T12:58:37.
- Test cutoff: 2026-04-28T07:41:43.
- Calibration 6,772; train 11,288; future test 4,516.
- Future scheduled_visit rate 20.77%.

> El commit 35bfd6f se conserva como historia, pero ya no es la fuente autoritativa.

## Clusterers seleccionados actuales

| Familia | Método | K | Min | Max | ARI |
|---|---|---:|---:|---:|---:|
| Lead | K-Means | 6 | 7.5% | 43.7% | 0.659 |
| Lead Persona | **Bisecting** | **7** | 8.4% | 22.8% | **1.000** |
| Search Need | K-Means | 3 | 23.7% | 46.3% | **1.000** |
| Spot | Bisecting | 7 | 9.5% | 27.3% | 0.410 |
| Broker | Bisecting | 7 | 7.0% | 22.0% | 0.443 |
| Inquiry Intent | **K-Means** | **7** | 13.1% | 15.8% | **0.998** |

## Señal predictiva actual

| Modelo | AUC | AP | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|
| Global | 0.5000 | 0.2077 | 1.000x | 20.0% |
| E001 balanced profiles | **0.5129** | **0.2123** | **1.033x** | 20.8% |
| E002 Persona + Need | 0.4963 | 0.2054 | 1.001x | 18.8% |
| E003 + Intent | 0.5017 | 0.2060 | 0.948x | 18.9% |

- E002 vs E001 ΔAP **-0.00678**, IC95% **[-0.02245, +0.00719]**.
- E003 vs E002 ΔAP **+0.00155**, IC95% **[-0.01163, +0.01391]**.

## Interpretabilidad actualizada

### Persona
La lectura anterior P1=tenant/P2=broker/P3=historial ya no corresponde al artifact actual.

- P1 organic.
- P2 paid.
- P3 referral.
- P4 prior_searches alta.
- P5 has_converted_before + prior_inquiries alta.
- P6 email.
- P7 social.

**Lectura:** principalmente Acquisition Channel + Behavioral Maturity; no una persona comercial pura.

### Search Need
- N1 renta.
- N2 venta.
- N3 both + mayor área.

**Lectura:** faceta semánticamente limpia y accionable.

### Spot
S2/S3/S5/S6/S7 son esencialmente geográficos; S4 es físico. Esto soporta separar Physical Space de Location.

### Inquiry Intent
I1–I7 equivalen casi exactamente a un día de semana distinto.

**Lectura:** no representa intención comercial y no debe usarse como perfil operativo.

## Evidencia fuente

- [summary.json](../profile_clustering_v2/results/summary.json)
- [selected_clusterers.csv](../profile_clustering_v2/results/selected_clusterers.csv)
- [profile_interpretability.csv](../profile_clustering_v2/results/profile_interpretability.csv)
- [model_metrics.csv](../profile_clustering_v2/results/model_metrics.csv)
- [bootstrap_deltas.csv](../profile_clustering_v2/results/bootstrap_deltas.csv)

La continuación de esta línea está en [EV-010](EV-010_matching_ab_v3.md) y [INTERPRETABILIDAD](../matching_ab_v3/INTERPRETABILIDAD.md).
