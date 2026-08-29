# Clustering benchmark v2 — perfiles interpretables y compatibilidad

## Resumen ejecutivo

Se repitió el experimento con una metodología más estricta y con cuatro familias de clustering: **K-Means, Bisecting K-Means, BIRCH y Gaussian Mixture**, evaluadas entre K=3 y K=7.

La selección de clusters **no usa el outcome**. Combina separación, balance y estabilidad. Además, la línea temporal se divide en tres ventanas:

1. **Profile calibration**: primeros 30% de inquiries; descubre y congela los perfiles.
2. **Predictive train**: tramo intermedio hasta el 80%.
3. **Future test**: 20% final, completamente fuera de muestra.

Esto corrige el look-ahead del experimento anterior en los perfiles históricos del broker.

- Profile cutoff: **2025-09-29T12:58:37**
- Test cutoff: **2026-04-28T07:41:43**
- Calibration inquiries: **6,772**
- Predictive train inquiries: **11,288**
- Future test inquiries: **4,516**
- Future scheduled-visit rate: **20.8%**

> `scheduled_visit` sigue siendo un proxy de avance comercial. El dataset público no contiene la venta/cierre real.

## 1. ¿Se resolvió el problema del cluster de ~90%?

### Clusterers seleccionados

| profile_family | method | k | silhouette | min_cluster_share | max_cluster_share | normalized_entropy | stability_ari | balance_ok | selection_score |
|---|---|---|---|---|---|---|---|---|---|
| broker | bisecting | 7 | 0.023 | 0.070 | 0.220 | 0.974 | 0.443 | True | 0.290 |
| inquiry_intent | kmeans | 7 | 0.155 | 0.131 | 0.158 | 0.999 | 0.998 | True | 0.494 |
| lead | kmeans | 6 | 0.098 | 0.075 | 0.437 | 0.866 | 0.659 | True | 0.368 |
| lead_persona | bisecting | 7 | 0.115 | 0.084 | 0.228 | 0.956 | 1.000 | True | 0.445 |
| search_need | kmeans | 3 | 0.062 | 0.237 | 0.463 | 0.964 | 1.000 | True | 0.394 |
| spot | bisecting | 7 | 0.088 | 0.095 | 0.273 | 0.965 | 0.410 | True | 0.350 |

El criterio `balance_ok` exige simultáneamente **cluster mínimo >= 5%** y **cluster máximo <= 70%**. Si una familia no consigue una solución así, se conserva la mejor alternativa pero se marca explícitamente.

### Interpretabilidad de perfiles

| profile_family | profile_id | n_reference | share_reference | top_signals |
|---|---|---|---|---|
| lead | L1 | 1070 | 0.437 | preferred_state=CDMX (27%; +14%pp) / preferred_municipality=Querétaro (18%; +9%pp) |
| lead | L2 | 485 | 0.198 | preferred_state=Estado de México (62%; +48%pp) / preferred_municipality=León (36%; +28%pp) / preferred_corridor=centro-leon (34%; +26%pp) |
| lead | L3 | 277 | 0.113 | preferred_state=Jalisco (100%; +88%pp) / preferred_municipality=Zapopan (52%; +46%pp) / preferred_corridor=andares-puerta-hierro (48%; +42%pp) |
| lead | L4 | 245 | 0.100 | prior_searches alto (44.00; +6.00 IQR) |
| lead | L5 | 190 | 0.078 | preferred_state=Puebla (100%; +92%pp) / preferred_municipality=Puebla (100%; +92%pp) / preferred_corridor=angelopolis-lomas (92%; +85%pp) |
| lead | L6 | 184 | 0.075 | preferred_state=Yucatán (100%; +92%pp) / preferred_municipality=Mérida (100%; +92%pp) / preferred_corridor=paseo-montejo (92%; +84%pp) |
| lead_persona | P1 | 560 | 0.228 | source=organic (100%; +72%pp) / prior_inquiries bajo (0.00; -0.29 IQR) |
| lead_persona | P2 | 498 | 0.203 | source=paid (100%; +74%pp) |
| lead_persona | P3 | 488 | 0.199 | source=referral (80%; +59%pp) |
| lead_persona | P4 | 268 | 0.109 | prior_searches alto (42.50; +5.79 IQR) |
| lead_persona | P5 | 223 | 0.091 | has_converted_before=True (62%; +49%pp) / prior_inquiries alto (82.00; +11.43 IQR) |
| lead_persona | P6 | 207 | 0.084 | source=email (100%; +90%pp) |
| lead_persona | P7 | 207 | 0.084 | source=social (100%; +90%pp) / prior_inquiries bajo (0.00; -0.29 IQR) |
| search_need | N1 | 1135 | 0.463 | search_modality=rent (99%; +50%pp) / min_budget_mxn_sale_total alto (22246852.63; +0.59 IQR) / max_budget_mxn_sale_total alto (29597585.10; +0.58 IQR) |
| search_need | N2 | 735 | 0.300 | search_modality=sale (100%; +69%pp) |
| search_need | N3 | 581 | 0.237 | search_modality=both (83%; +63%pp) / target_area_sqm alto (479.20; +0.20 IQR) |
| spot | S1 | 504 | 0.273 | region=noroeste (30%; +20%pp) / state=Yucatán (19%; +13%pp) / municipality=Mérida (19%; +13%pp) |
| spot | S2 | 277 | 0.150 | state=CDMX (100%; +83%pp) / region=centro (100%; +71%pp) / municipality=Cuauhtémoc (35%; +29%pp) / amenities_count alto (2.00; +0.33 IQR) |
| spot | S3 | 259 | 0.140 | region=bajío (100%; +83%pp) / state=Querétaro (66%; +55%pp) / municipality=Querétaro (66%; +55%pp) |
| spot | S4 | 252 | 0.137 | floor_level alto (15.00; +5.00 IQR) / elevators alto (9.50; +0.81 IQR) |
| spot | S5 | 191 | 0.104 | state=Nuevo León (100%; +88%pp) / region=noreste (100%; +88%pp) / municipality=San Pedro Garza García (53%; +47%pp) |
| spot | S6 | 187 | 0.101 | state=Estado de México (99%; +88%pp) / region=centro (100%; +71%pp) / municipality=Naucalpan de Juárez (54%; +48%pp) |
| spot | S7 | 175 | 0.095 | state=Jalisco (100%; +89%pp) / region=occidente (100%; +89%pp) / municipality=Zapopan (52%; +46%pp) |
| broker | B1 | 66 | 0.220 | share_modality_sale alto (0.32; +0.48 IQR) / fast_rate bajo (0.32; -0.45 IQR) / share_region_centro alto (0.40; +0.40 IQR) |
| broker | B2 | 50 | 0.167 | share_region_centro alto (0.41; +0.45 IQR) / share_modality_rent alto (0.50; +0.34 IQR) / median_response_hours bajo (7.10; -0.30 IQR) |
| broker | B3 | 48 | 0.160 | share_region_noroeste alto (0.20; +1.20 IQR) / share_region_norte alto (0.12; +0.94 IQR) / share_region_occidente alto (0.14; +0.71 IQR) |
| broker | B4 | 46 | 0.153 | median_sale bajo (20568.96; -0.84 IQR) / median_rent bajo (138.20; -0.75 IQR) / share_region_occidente alto (0.11; +0.56 IQR) |
| broker | B5 | 38 | 0.127 | share_region_centro-norte alto (0.20; +2.15 IQR) / share_region_noreste bajo (0.00; -0.53 IQR) / share_modality_rent alto (0.50; +0.34 IQR) |
| broker | B6 | 31 | 0.103 | share_region_sureste alto (0.20; +1.80 IQR) / share_region_occidente alto (0.17; +0.83 IQR) / share_region_noreste bajo (0.00; -0.53 IQR) |
| broker | B7 | 21 | 0.070 | share_region_occidente alto (0.33; +1.67 IQR) / share_sector_name_industrial bajo (0.00; -1.04 IQR) / share_region_centro bajo (0.00; -1.00 IQR) |
| inquiry_intent | I1 | 1068 | 0.158 | inquiry_weekday=Saturday (96%; +81%pp) |
| inquiry_intent | I2 | 993 | 0.147 | inquiry_weekday=Friday (100%; +85%pp) |
| inquiry_intent | I3 | 978 | 0.144 | inquiry_weekday=Monday (100%; +85%pp) |
| inquiry_intent | I4 | 958 | 0.141 | inquiry_weekday=Tuesday (100%; +86%pp) |
| inquiry_intent | I5 | 953 | 0.141 | inquiry_weekday=Sunday (100%; +86%pp) |
| inquiry_intent | I6 | 938 | 0.139 | inquiry_weekday=Thursday (100%; +86%pp) |
| inquiry_intent | I7 | 884 | 0.131 | inquiry_weekday=Wednesday (100%; +86%pp) |

Los nombres no se asignan con el target. `top_signals` compara cada cluster contra su población de calibración y muestra las características que más lo distinguen.

## 2. ¿Alguna representación aumenta el lift?

| model | roc_auc | average_precision | brier | log_loss | lift_top_10pct | recall_top_20pct |
|---|---|---|---|---|---|---|
| global_baseline | 0.500 | 0.208 | 0.165 | 0.511 | 1.000 | 0.200 |
| E001_balanced_profiles | 0.513 | 0.212 | 0.166 | 0.515 | 1.033 | 0.208 |
| E002_lead_facets | 0.496 | 0.205 | 0.168 | 0.521 | 1.001 | 0.188 |
| E003_inquiry_intent | 0.502 | 0.206 | 0.168 | 0.521 | 0.948 | 0.189 |

- **E001**: Lead + Spot + Broker con clustering multi-método balanceado.
- **E002**: separa Lead en **Lead Persona + Search Need**, manteniendo Spot + Broker.
- **E003**: agrega **Inquiry Intent** en T1.

### Incertidumbre de los cambios

| comparison | delta_auc | delta_auc_low | delta_auc_high | delta_ap | delta_ap_low | delta_ap_high | delta_lift10 | delta_lift10_low | delta_lift10_high |
|---|---|---|---|---|---|---|---|---|---|
| E002_vs_E001 | -0.016 | -0.043 | 0.008 | -0.007 | -0.022 | 0.007 | -0.020 | -0.262 | 0.218 |
| E003_vs_E002 | 0.007 | -0.014 | 0.028 | 0.002 | -0.012 | 0.014 | -0.060 | -0.251 | 0.170 |

**Mejor modelo por Average Precision: E001_balanced_profiles**.

## 3. Compatibilidad de perfiles

### Lead × Spot × Broker

| lead_profile | spot_profile | broker_profile | n | scheduled_visit_rate | smoothed_visit_rate | lift_vs_global | expected_model_probability | residual_synergy | wilson_low | wilson_high |
|---|---|---|---|---|---|---|---|---|---|---|
| L1 | S5 | B2 | 35 | 0.343 | 0.271 | 1.304 | 0.185 | 0.086 | 0.208 | 0.508 |
| L6 | S1 | B1 | 40 | 0.300 | 0.254 | 1.222 | 0.169 | 0.085 | 0.181 | 0.454 |
| L2 | S1 | B3 | 41 | 0.195 | 0.201 | 0.969 | 0.135 | 0.067 | 0.102 | 0.340 |
| L1 | S1 | B5 | 93 | 0.301 | 0.273 | 1.314 | 0.207 | 0.066 | 0.217 | 0.401 |
| L1 | S2 | B4 | 55 | 0.273 | 0.245 | 1.181 | 0.188 | 0.057 | 0.173 | 0.402 |
| L2 | S1 | B1 | 56 | 0.232 | 0.222 | 1.069 | 0.170 | 0.052 | 0.141 | 0.358 |
| L1 | S3 | B3 | 53 | 0.189 | 0.197 | 0.948 | 0.146 | 0.051 | 0.106 | 0.314 |
| L1 | S4 | B6 | 33 | 0.242 | 0.223 | 1.076 | 0.173 | 0.050 | 0.128 | 0.410 |
| L6 | S1 | B3 | 30 | 0.200 | 0.204 | 0.984 | 0.160 | 0.044 | 0.095 | 0.373 |
| L1 | S4 | B5 | 48 | 0.125 | 0.163 | 0.783 | 0.122 | 0.041 | 0.059 | 0.247 |
| L1 | S6 | B1 | 36 | 0.250 | 0.228 | 1.096 | 0.189 | 0.039 | 0.138 | 0.411 |
| L1 | S3 | B1 | 68 | 0.221 | 0.216 | 1.039 | 0.181 | 0.035 | 0.138 | 0.333 |

### Search Need × Spot

| need_profile | spot_profile | n | scheduled_visit_rate | smoothed_visit_rate | lift_vs_global | expected_model_probability | residual_synergy |
|---|---|---|---|---|---|---|---|
| N2 | S5 | 155 | 0.232 | 0.227 | 1.094 | 0.159 | 0.069 |
| N1 | S6 | 172 | 0.244 | 0.237 | 1.142 | 0.188 | 0.050 |
| N2 | S4 | 159 | 0.208 | 0.208 | 0.999 | 0.177 | 0.031 |
| N1 | S4 | 317 | 0.211 | 0.211 | 1.016 | 0.181 | 0.030 |
| N1 | S5 | 157 | 0.248 | 0.240 | 1.156 | 0.213 | 0.027 |
| N1 | S3 | 337 | 0.214 | 0.213 | 1.026 | 0.187 | 0.026 |
| N2 | S7 | 103 | 0.214 | 0.212 | 1.020 | 0.191 | 0.021 |
| N3 | S6 | 128 | 0.227 | 0.222 | 1.069 | 0.201 | 0.021 |
| N3 | S1 | 314 | 0.226 | 0.224 | 1.079 | 0.207 | 0.017 |
| N2 | S3 | 197 | 0.254 | 0.246 | 1.184 | 0.230 | 0.016 |
| N1 | S1 | 644 | 0.213 | 0.212 | 1.023 | 0.197 | 0.016 |
| N1 | S7 | 250 | 0.188 | 0.191 | 0.918 | 0.176 | 0.015 |

### Inquiry Intent × Search Need

| intent_profile | need_profile | n | scheduled_visit_rate | smoothed_visit_rate | lift_vs_global | expected_model_probability | residual_synergy |
|---|---|---|---|---|---|---|---|
| I4 | N1 | 342 | 0.222 | 0.221 | 1.063 | 0.170 | 0.051 |
| I1 | N3 | 154 | 0.266 | 0.254 | 1.224 | 0.215 | 0.039 |
| I2 | N1 | 290 | 0.231 | 0.228 | 1.099 | 0.192 | 0.036 |
| I7 | N2 | 174 | 0.190 | 0.193 | 0.929 | 0.157 | 0.036 |
| I6 | N2 | 176 | 0.256 | 0.247 | 1.188 | 0.212 | 0.035 |
| I7 | N1 | 333 | 0.216 | 0.215 | 1.037 | 0.182 | 0.033 |
| I1 | N1 | 286 | 0.224 | 0.222 | 1.068 | 0.196 | 0.026 |
| I2 | N3 | 151 | 0.205 | 0.206 | 0.991 | 0.182 | 0.024 |
| I7 | N3 | 168 | 0.220 | 0.218 | 1.049 | 0.195 | 0.022 |
| I3 | N2 | 198 | 0.237 | 0.232 | 1.119 | 0.215 | 0.018 |
| I6 | N1 | 291 | 0.196 | 0.197 | 0.950 | 0.182 | 0.016 |
| I1 | N2 | 168 | 0.202 | 0.203 | 0.979 | 0.189 | 0.015 |

### Inquiry Intent × Broker

| intent_profile | broker_profile | n | scheduled_visit_rate | smoothed_visit_rate | lift_vs_global | expected_model_probability | residual_synergy |
|---|---|---|---|---|---|---|---|
| I3 | B7 | 37 | 0.297 | 0.251 | 1.207 | 0.150 | 0.100 |
| I1 | B6 | 55 | 0.236 | 0.224 | 1.080 | 0.129 | 0.096 |
| I2 | B3 | 138 | 0.239 | 0.232 | 1.117 | 0.145 | 0.087 |
| I7 | B7 | 38 | 0.184 | 0.196 | 0.945 | 0.117 | 0.079 |
| I4 | B5 | 64 | 0.188 | 0.195 | 0.940 | 0.129 | 0.066 |
| I7 | B4 | 71 | 0.239 | 0.228 | 1.098 | 0.167 | 0.061 |
| I2 | B1 | 147 | 0.265 | 0.253 | 1.218 | 0.193 | 0.060 |
| I7 | B2 | 90 | 0.256 | 0.241 | 1.159 | 0.189 | 0.052 |
| I3 | B5 | 81 | 0.222 | 0.217 | 1.047 | 0.167 | 0.051 |
| I1 | B1 | 107 | 0.243 | 0.233 | 1.124 | 0.183 | 0.050 |
| I4 | B1 | 160 | 0.212 | 0.212 | 1.018 | 0.167 | 0.045 |
| I3 | B3 | 100 | 0.250 | 0.238 | 1.145 | 0.194 | 0.044 |

`residual_synergy` compara la tasa suavizada observada del grupo contra la probabilidad que ya esperaba el modelo correspondiente. Es una señal exploratoria; no implica causalidad.

## 4. ¿Qué otras entidades/facetas vale la pena perfilar?

| candidate | status | tested | why |
|---|---|---|---|
| Lead Persona | PROFILE | True | Separates actor characteristics from the commercial requirement; stable at T1. |
| Search Need | PROFILE | True | Represents sector/modality/area/budget/geography requested; directly relevant to matching. |
| Inquiry Intent | PROFILE_AT_T1 | True | Captures channel, visit intent, urgency and requested parameters; only exists after inquiry. |
| Market Context | CONTEXT_NOT_ENTITY | False | Potentially useful regime, but monthly timestamp does not prove publication availability; excluded from governed predictive test. |
| Availability Snapshot | DIRECT_STATE | False | Use latest non-future availability directly; clustering would hide operational meaning. |
| Spot Attributes | MERGED_INTO_SPOT | True | 1:1 extension of Spot, already included in Spot archetype. |
| Geography | DIMENSION | False | Useful for matching/context, but not a standalone behavioral entity. |

La recomendación conceptual es:

- **Sí** perfilar `Lead Persona`, `Search Need`, `Spot` y `Broker`.
- **Sí, pero sólo en T1**, perfilar `Inquiry Intent`.
- **No** separar `Spot Attributes`: son una extensión 1:1 de Spot.
- **No** clusterizar `Availability Snapshot`: conviene usar disponibilidad como estado temporal directo.
- **Market Context** puede convertirse en un `Market Regime`, pero no se usa aquí porque la fecha mensual no demuestra cuándo estaba publicado. Incluirlo sin esa semántica rompería el contrato de leakage.

## 5. Leakage y trazabilidad

- Los clusterers se aprenden sólo en la ventana temprana de calibración.
- Los perfiles del broker usan únicamente spots e inquiries anteriores al `profile_cutoff`.
- Esos perfiles se congelan antes del entrenamiento predictivo.
- `lead_score_internal`, `days_on_market`, `total_inquiries`, `total_views` e `is_active` no entran en los perfiles.
- `broker_response` sólo define el target; `broker_response_hours` sólo se usa en la ventana histórica de calibración del broker.
- Inquiry Intent usa únicamente información disponible en `inquiry_at`.
- Los experimentos E001→E002→E003 usan el harness del repo y tienen contratos comparables.

## 6. Calidad de joins

- Leads: **5,000**
- Spots: **3,000**
- Brokers observados: **300**
- Inquiries: **22,576**
- inquiry→lead: **100.0%**
- inquiry→spot: **100.0%**
- spot→attributes: **100.0%**

## 7. Archivos

- `results/clustering_benchmark.csv`: todos los métodos/K probados.
- `results/selected_clusterers.csv`: clusterer seleccionado por familia.
- `results/profile_interpretability.csv`: explicación de cada cluster.
- `results/model_metrics.csv`: comparación E001/E002/E003.
- `results/bootstrap_deltas.csv`: incertidumbre de cambios.
- `results/*_performance.csv`: compatibilidades con soporte.
- `results/*_assignments.csv`: asignación de perfiles.
- `results/E00*_results.json`: contratos de resultados para el harness.

## Conclusión

La decisión no debe ser “tener clusters balanceados a cualquier costo”. Un perfil útil necesita **separación + tamaño suficiente + estabilidad + significado de negocio + señal futura**. Esta versión evalúa esas cinco condiciones por separado.

Si E003 mejora fuera de muestra, `Inquiry Intent` merece convertirse en una capa dinámica del journey. Si E002 mejora sin E003, la ganancia viene de separar **quién es el lead** de **qué necesita**. Si ninguna mejora, los perfiles siguen siendo útiles descriptivamente, pero no deben multiplicar el Opportunity Score.
