# Matching A/B v3 — relational audit + two governed experiments

## Executive result

Data-quality gate: **PASS** with 0 critical failures.
The suite audited all six candidate tables before fitting any model and used cross-table joins, temporal checks, business rules and point-in-time availability.

- E006 conclusion: **INCONCLUSIVE**. Delta AP B−A -0.0000 (95% cluster-bootstrap CI -0.0057 to +0.0055).
- E007 conclusion: **INCONCLUSIVE**. Delta AP B−A +0.0021 (95% cluster-bootstrap CI -0.0096 to +0.0129).

The offline comparisons are **pre-experiment evidence only**. A causal A/B requires the randomized lead-level protocols saved in results/online_ab_protocols.json.

## Relational/data audit

- Leads: 5,000; Spots: 3,000; Spot attributes: 3,000; Inquiries: 22,576; Availability snapshots: 30,000; Market-context rows: 500.
- Availability backward-as-of coverage: 92.4%; coverage with lag <=90d: 88.5%.
- Exact same-month market-context coverage at Spot geography/sector grain: 23.8%. It is **not used** as a historical feature because publication semantics are unknown.
- Actual inquiry lead↔spot modality compatibility: 100.0%; sector exact match: 70.4%; preferred municipality exact match: 19.8%; declared corridor exact match: 18.6%.

See relationship_checks.csv, content_consistency_checks.csv and column_completeness.csv for the full evidence rather than relying on a dry single-table profile.

## Spot decomposition

| profile_family   | method   |   k |   silhouette |   min_cluster_share |   max_cluster_share |   normalized_entropy |   stability_ari | balance_ok   |   selection_score | selected   |
|:-----------------|:---------|----:|-------------:|--------------------:|--------------------:|---------------------:|----------------:|:-------------|------------------:|:-----------|
| PH               | gmm      |   4 |     0.127796 |           0.0661247 |            0.511111 |             0.841215 |        0.688727 | True         |          0.499348 | True       |
| LOC              | kmeans   |   7 |     0.478333 |           0.0585366 |            0.333875 |             0.90482  |        1        | True         |          0.909297 | True       |

### Interpretable profiles

| profile_id   |   n |     share | interpretation                                                                                                                                                                                                                                | profile_family   |
|:-------------|----:|----------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
| PH1          | 943 | 0.511111  | sector_name=Office (52%) | type_name=Single (70%) | modality=rent (38%) | natural_light=True (75%) | security_type=basic (39%) | area_sqm median=124.70 | luminaires median=2.00 | charging_ports median=0.00 | floor_level median=0.00       | physical         |
| PH2          | 488 | 0.264499  | sector_name=Industrial (100%) | type_name=Single (72%) | modality=rent (42%) | natural_light=True (57%) | security_type=basic (43%) | area_sqm median=2841.85 | luminaires median=2.00 | charging_ports median=0.00 | floor_level median=0.00 | physical         |
| PH3          | 292 | 0.158266  | sector_name=Land (100%) | type_name=Single (68%) | modality=rent (40%) | natural_light=True (73%) | security_type=basic (42%) | area_sqm median=4613.55 | luminaires median=2.00 | charging_ports median=0.00 | floor_level median=1.00       | physical         |
| PH4          | 122 | 0.0661247 | sector_name=Office (48%) | type_name=Single (65%) | modality=rent (48%) | natural_light=True (81%) | security_type=basic (36%) | area_sqm median=2247.95 | luminaires median=2.50 | charging_ports median=3.00 | floor_level median=1.00      | physical         |
| LOC1         | 616 | 0.333875  | state=CDMX (52%) | municipality=Naucalpan de Juárez (19%) | settlement=Lomas Verdes (19%) | corridor=lomas-verdes-satelite (19%) | region=centro (88%) | lat median=19.41 | lon median=-99.18                                                 | location         |
| LOC2         | 402 | 0.217886  | state=Querétaro (50%) | municipality=Querétaro (50%) | settlement=Juriquilla (27%) | corridor=juriquilla-juncos (27%) | region=bajío (76%) | lat median=20.73 | lon median=-100.47                                                            | location         |
| LOC3         | 222 | 0.120325  | state=Nuevo León (100%) | municipality=San Pedro Garza García (51%) | settlement=Del Valle (51%) | corridor=vasconcelos-calzada (51%) | region=noreste (100%) | lat median=25.67 | lon median=-100.34                                         | location         |
| LOC4         | 201 | 0.108943  | state=Jalisco (100%) | municipality=Zapopan (51%) | settlement=Puerta de Hierro (51%) | corridor=andares-puerta-hierro (51%) | region=occidente (100%) | lat median=20.69 | lon median=-103.39                                                | location         |
| LOC5         | 184 | 0.099729  | state=Baja California (51%) | municipality=Tijuana (51%) | settlement=Zona Río (51%) | corridor=zona-rio-aguacaliente (51%) | region=noroeste (100%) | lat median=32.49 | lon median=-117.01                                                  | location         |
| LOC6         | 112 | 0.0607046 | state=Chihuahua (100%) | municipality=Chihuahua (100%) | settlement=Centro (100%) | corridor=centro-chihuahua (100%) | region=norte (100%) | lat median=28.64 | lon median=-106.09                                                            | location         |
| LOC7         | 108 | 0.0585366 | state=Yucatán (100%) | municipality=Mérida (100%) | settlement=Centro (100%) | corridor=paseo-montejo (100%) | region=sureste (100%) | lat median=20.98 | lon median=-89.62                                                                   | location         |

## Offline A/B metrics

| model                             |   roc_auc |   average_precision |    brier |   log_loss |   lift_top_10pct |   recall_top_20pct |   lead_level_ap |   lead_level_auc |   lead_level_n |   lead_level_visit_rate |
|:----------------------------------|----------:|--------------------:|---------:|-----------:|-----------------:|-------------------:|----------------:|-----------------:|---------------:|------------------------:|
| E006_A_unified_spot               |  0.499956 |            0.20996  | 0.165167 |   0.512885 |          1.02255 |           0.19403  |        0.372789 |         0.544101 |           2065 |                0.343341 |
| E006_B_physical_plus_location     |  0.498455 |            0.209809 | 0.165171 |   0.512908 |          1.00125 |           0.197228 |        0.3752   |         0.546902 |           2065 |                0.343341 |
| E007_A_marginals                  |  0.498455 |            0.209809 | 0.165171 |   0.512908 |          1.00125 |           0.197228 |        0.3752   |         0.546902 |           2065 |                0.343341 |
| E007_B_compatibility_interactions |  0.498462 |            0.211706 | 0.166271 |   0.516831 |          1.0332  |           0.206823 |        0.426993 |         0.5899   |           2065 |                0.343341 |

## Paired uncertainty

Bootstrap resamples **lead_id clusters**, not individual inquiries, preserving within-lead dependence.

| comparison   |    delta_auc |   delta_auc_low |   delta_auc_high |     delta_ap |   delta_ap_low |   delta_ap_high |   delta_lift10 |   delta_lift10_low |   delta_lift10_high |
|:-------------|-------------:|----------------:|-----------------:|-------------:|---------------:|----------------:|---------------:|-------------------:|--------------------:|
| E006_B_vs_A  | -0.00139472  |      -0.0102006 |       0.00573097 | -4.62563e-05 |    -0.00572166 |      0.00550305 |     0.00564989 |          -0.126822 |            0.124141 |
| E007_B_vs_A  |  0.000114236 |      -0.0187963 |       0.02004    |  0.0020508   |    -0.00960449 |      0.0129438  |     0.0224512  |          -0.186325 |            0.225589 |

## Compatibility cells

| interaction              |   n |   visit_rate |   smoothed_rate |   lift_vs_global | need_profile   | physical_profile   | location_profile   | broker_profile   |
|:-------------------------|----:|-------------:|----------------:|-----------------:|:---------------|:-------------------|:-------------------|:-----------------|
| need_x_physical_x_broker |  73 |     0.315068 |        0.283798 |          1.36634 | N2             | PH1                | nan                | B6               |
| need_x_physical_x_broker |  81 |     0.296296 |        0.272353 |          1.31124 | N3             | PH1                | nan                | B5               |
| need_x_location          |  64 |     0.296875 |        0.268417 |          1.29229 | N3             | nan                | LOC6               | nan              |
| physical_x_broker        |  99 |     0.282828 |        0.265358 |          1.27757 | nan            | PH3                | nan                | B2               |
| physical_x_broker        | 139 |     0.273381 |        0.261723 |          1.26006 | nan            | PH3                | nan                | B1               |
| need_x_physical_x_broker |  67 |     0.283582 |        0.260115 |          1.25232 | N2             | PH2                | nan                | B3               |
| physical_x_broker        | 184 |     0.255435 |        0.248744 |          1.19758 | nan            | PH2                | nan                | B3               |
| need_x_location          | 258 |     0.248062 |        0.243858 |          1.17406 | N2             | nan                | LOC2               | nan              |
| need_x_physical_x_broker |  78 |     0.25641  |        0.242881 |          1.16935 | N1             | PH2                | nan                | B3               |
| need_x_broker            | 132 |     0.25     |        0.242168 |          1.16592 | N3             | nan                | nan                | B5               |
| need_x_broker            |  66 |     0.257576 |        0.241991 |          1.16507 | N2             | nan                | nan                | B7               |
| need_x_broker            | 112 |     0.25     |        0.241065 |          1.16061 | N2             | nan                | nan                | B6               |
| physical_x_broker        | 303 |     0.244224 |        0.240934 |          1.15998 | nan            | PH1                | nan                | B5               |
| need_x_physical_x_broker |  96 |     0.25     |        0.23993  |          1.15514 | N2             | PH1                | nan                | B2               |
| need_x_physical_x_broker |  92 |     0.25     |        0.2396   |          1.15355 | N1             | PH3                | nan                | B4               |

## Complete online A/B design

Both experiments are pre-registered as 50/50 sticky lead-level randomized tests, stratified by sector, modality and lead type. Primary analysis is ITT after a fixed 30-day maturation window.

### Power

Baseline future lead-level rate: 34.3%; unique future-test leads: 2,065.

|   baseline_rate |   absolute_mde |   relative_lift |   n_per_arm |   total_n |
|----------------:|---------------:|----------------:|------------:|----------:|
|        0.343341 |          0.01  |       0.0291255 |       35633 |     71266 |
|        0.343341 |          0.015 |       0.0436883 |       15889 |     31778 |
|        0.343341 |          0.02  |       0.0582511 |        8966 |     17932 |
|        0.343341 |          0.025 |       0.0728138 |        5756 |     11512 |
|        0.343341 |          0.03  |       0.0873766 |        4010 |      8019 |

## Interpretation rules

1. No offline result is called causal.
2. E006 changes only the Spot representation between A and B; common availability features are identical.
3. E007 changes only the interaction terms between A and B.
4. Availability is joined with the latest snapshot_date <= inquiry_at.
5. Market Context is audited but excluded until publication/effective-time semantics are defensible.
6. scheduled_visit is commercial-progress proxy, not hidden true conversion/sale.
