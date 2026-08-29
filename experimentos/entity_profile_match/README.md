# Experimento: perfiles Lead × Spot × Broker

## Resumen ejecutivo

**No hay evidencia robusta de química adicional entre perfiles fuera de muestra.**

La hipótesis es que un lead no tiene una probabilidad fija de avanzar: parte de la oportunidad puede depender del tipo de inmueble y del tipo de broker con el que se conecta. Los perfiles se aprenden de forma no supervisada y la compatibilidad se evalúa en un periodo futuro.

> Importante: el dataset público del candidato no contiene cierre o venta real. El outcome primario aquí es scheduled_visit y el secundario es respuesta positiva (accepted o scheduled_visit). Una visita es un proxy de avance comercial, no una venta.

- Corte temporal: **2026-04-28T07:41:43**.
- Train: **18,060 inquiries**; test futuro: **4,516 inquiries**.
- Tasa de visita en test: **20.8%**.
- Perfiles individuales: ROC AUC **0.503**, AP **0.208**.
- Perfiles + interacciones: ROC AUC **0.496**, AP **0.206**.
- Delta ROC AUC: **-0.006** (bootstrap 95% CI -0.040 a +0.023).
- Delta AP: **-0.002** (bootstrap 95% CI -0.013 a +0.009).

## Cómo se construyen los perfiles

K-Means sobre variables mixtas con imputación, one-hot encoding y escalado robusto. Se prueba K=3 a 8 y se elige por silhouette, evitando cuando es posible clusters menores a 3%.

### Selección de K

| entity | k | silhouette | min_cluster_share |
|---|---|---|---|
| lead | 3 | 0.784 | 0.011 |
| spot | 4 | 0.638 | 0.005 |
| broker | 3 | 0.102 | 0.037 |

### Lead profiles

Usan quién busca, sector y modalidad deseados, tamaño, presupuesto, ubicación preferida, fuente e historia previa. Se excluye lead_score_internal.

| profile_id | profile_name | n_reference | share_reference | median_target_area_sqm | median_prior_inquiries | prior_conversion_rate |
|---|---|---|---|---|---|---|
| L1 | L1 · tenant_direct / Retail / rent / mid-size | 3951 | 0.895 | 358.900 | 1.000 | 0.129 |
| L2 | L2 · broker / Office / sale / large-area | 416 | 0.094 | 802.500 | 1.000 | 0.154 |
| L3 | L3 · tenant_direct / Office / sale / large-area | 49 | 0.011 | 1587.500 | 0.000 | 0.143 |

### Spot profiles

Usan sector, modalidad, tipo, ubicación, área, precio y atributos físicos. Se excluyen days_on_market, total_inquiries, total_views e is_active.

| profile_id | profile_name | n_reference | share_reference | median_area_sqm | median_rent_price_sqm | median_sale_price_sqm |
|---|---|---|---|---|---|---|
| S1 | S1 · Office / rent / Single / mid-size | 2546 | 0.928 | 486.650 | 225.615 | 40229.325 |
| S2 | S2 · Industrial / both / Single / large-area | 120 | 0.044 | 10853.750 | 164.050 | 28206.280 |
| S3 | S3 · Industrial / rent / Single / large-area | 64 | 0.023 | 21519.400 | 139.430 | n/a |
| S4 | S4 · Industrial / both / Single / large-area | 14 | 0.005 | 42096.300 | 155.720 | 29244.755 |

### Broker profiles

No existe una tabla brokers. El perfil se reconstruye por broker_id usando sólo historia anterior al corte: composición del portafolio, volumen histórico, velocidad de respuesta y tasas históricas suavizadas de visita/respuesta.

| profile_id | profile_name | n_reference | share_reference | median_spots_pre | median_inquiries_pre | median_response_hours | median_scheduled_visit_rate_pre |
|---|---|---|---|---|---|---|---|
| B1 | B1 · Office / mid-speed / mid-visit / mid-book | 153 | 0.510 | 9.000 | 59.000 | 8.900 | 0.192 |
| B2 | B2 · Industrial / mid-speed / mid-visit / large-book | 136 | 0.453 | 10.000 | 61.500 | 8.000 | 0.195 |
| B3 | B3 · Industrial / mid-speed / mid-visit / small-book | 11 | 0.037 | 6.000 | 36.000 | 8.550 | 0.188 |

## Prueba de compatibilidad

Se comparan: baseline global; modelo con lead_profile + spot_profile + broker_profile; y modelo que además agrega Lead×Spot, Lead×Broker, Spot×Broker y la combinación triple. Si el tercer modelo mejora fuera de muestra, hay evidencia de que importa la combinación y no sólo que un perfil individual sea fuerte.

| model | roc_auc | average_precision | brier | log_loss | lift_top_10pct |
|---|---|---|---|---|---|
| global_baseline | 0.500 | 0.208 | 0.165 | 0.511 | 1.140 |
| profile_marginals | 0.503 | 0.208 | 0.165 | 0.511 | 1.033 |
| profile_interactions | 0.496 | 0.206 | 0.165 | 0.512 | 0.991 |

La métrica synergy_vs_marginals compara la tasa de visita suavizada de cada combinación contra la probabilidad esperada usando sólo los tres perfiles individuales. Sólo se muestran combinaciones con al menos 25 interacciones futuras.

### Combinaciones con mayor sinergia

| lead_profile | spot_profile | broker_profile | n | scheduled_visit_rate | smoothed_visit_rate | lift_vs_global | expected_marginal_probability | synergy_vs_marginals | wilson_low | wilson_high |
|---|---|---|---|---|---|---|---|---|---|---|
| L1 | S3 | B2 | 41 | 0.293 | 0.257 | 1.236 | 0.186 | 0.071 | 0.176 | 0.445 |
| L2 | S1 | B2 | 160 | 0.225 | 0.222 | 1.070 | 0.196 | 0.027 | 0.167 | 0.296 |
| L2 | S1 | B1 | 223 | 0.224 | 0.222 | 1.070 | 0.196 | 0.026 | 0.174 | 0.283 |
| L1 | S1 | B1 | 1922 | 0.210 | 0.210 | 1.012 | 0.196 | 0.014 | 0.193 | 0.229 |
| L1 | S1 | B2 | 1692 | 0.204 | 0.205 | 0.985 | 0.196 | 0.009 | 0.186 | 0.224 |
| L1 | S1 | B3 | 145 | 0.186 | 0.190 | 0.914 | 0.192 | -0.002 | 0.131 | 0.257 |
| L1 | S2 | B2 | 100 | 0.210 | 0.209 | 1.008 | 0.216 | -0.007 | 0.142 | 0.300 |
| L1 | S2 | B1 | 92 | 0.196 | 0.199 | 0.956 | 0.217 | -0.018 | 0.127 | 0.288 |
| L1 | S3 | B1 | 50 | 0.140 | 0.165 | 0.796 | 0.187 | -0.021 | 0.070 | 0.262 |

## Protección contra leakage

- Corte temporal al 80% de inquiry_at.
- El comportamiento del broker se calcula sólo antes del corte.
- Lead y Spot se clusterizan con entidades existentes antes del corte y el transformador se aplica después a entidades nuevas.
- Se excluyen broker_response y broker_response_hours de los perfiles de Lead y Spot.
- Se excluyen acumulados actuales del Spot.
- has_converted_before se conserva porque representa historia previa declarada, no el resultado futuro de la inquiry actual.

## Calidad de joins

- Leads: 5,000; Spots: 3,000; Brokers: 300; Inquiries: 22,576.
- Cobertura inquiry→lead: 100.0%.
- Cobertura inquiry→spot: 100.0%.
- Cobertura spot→attributes: 100.0%.

## Outputs

Los CSV de perfiles, asignaciones, selección de K, métricas y compatibilidades quedan en la carpeta results junto con results.json.

## Ejecución

    python experimentos/entity_profile_match/run_experiment.py

GitHub Actions usa `.github/workflows/entity-profile-match-experiment.yml`. Los workflows son una excepción estructural porque GitHub sólo los reconoce dentro de `.github/workflows/`; el código, resultados y evidencia permanecen en `experimentos/`.

## Uso recomendado

Si la señal de interacción se sostiene, usaría estos perfiles como una capa de compatibilidad, no como reemplazo del Lead Opportunity Score:

**Opportunity = Lead Quality × Inventory Availability × Compatibility(Lead type, Spot type, Broker type)**

La compatibilidad debe regularizarse y volver a efectos marginales cuando una combinación tenga poco soporte. Para afirmar causalidad sobre routing o asignación de brokers hace falta un experimento posterior.
