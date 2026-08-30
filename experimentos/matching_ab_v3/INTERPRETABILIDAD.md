# Interpretabilidad completa — Matching A/B v3

Este documento es el diccionario de negocio de los perfiles utilizados en E006/E007 y de las combinaciones con mejor desempeño descriptivo en el future test.

> **Regla de lectura:** los nombres de cluster son descriptivos, no causales. Un cluster resume similitud multivariada; no significa que una sola variable “defina” al grupo ni que pertenecer al cluster cause una visita.

## 1. Familias de perfiles y uso

| Familia | IDs | Uso en E006/E007 | Lectura |
|---|---|---|---|
| Lead Persona | P1–P7 | Activa | Canal de adquisición + historial previo. **No es todavía una persona comercial pura.** |
| Search Need | N1–N3 | Activa | Necesidad comercial: renta, venta o flexible/both. |
| Unified Spot | S1–S7 | Sólo control E006 | Mezcla geografía y atributos físicos; se conserva para comparar contra la descomposición. |
| Physical Space | PH1–PH4 | Tratamiento E006/E007 | Arquetipo físico del inmueble sin geografía. |
| Location | LOC1–LOC7 | Tratamiento E006/E007 | Régimen/localización geográfica. |
| Broker | B1–B7 | Activa | Especialización de inventario/región/modalidad e historial. La parte de velocidad es de menor confianza por la inconsistencia de `broker_response_hours`. |
| Inquiry Intent | I1–I7 | No activa | Quedó dominada por día de semana; no se usa en E006/E007. |
| Lead agregado | L1–L6 | No activo | Fue reemplazado conceptualmente por Persona + Search Need. |

## 2. Lead Persona — P1 a P7

La familia Persona actual debe interpretarse con cautela: el rerun autoritativo quedó dominado por `source` y, en menor medida, historial. Por tanto, estos clusters son mejores como **acquisition/history personas** que como arquetipos comerciales finales.

| Cluster | N calibración | Share | Señales dominantes | Interpretación de negocio | Confianza semántica |
|---|---:|---:|---|---|---|
| **P1** | 560 | 22.8% | organic 100%; prior inquiries bajas | Lead orgánico, relativamente temprano en interacción | Media |
| **P2** | 498 | 20.3% | paid 100% | Lead proveniente de adquisición pagada | Media |
| **P3** | 488 | 19.9% | referral 80% | Lead principalmente referido | Media |
| **P4** | 268 | 10.9% | prior_searches alta, mediana 42.5 | Explorador recurrente / alta actividad de búsqueda | Alta |
| **P5** | 223 | 9.1% | has_converted_before 62%; prior_inquiries alta, mediana 82 | Lead experimentado, con historial de conversión/interacción | Alta |
| **P6** | 207 | 8.4% | email 100% | Lead originado por email | Media |
| **P7** | 207 | 8.4% | social 100%; prior inquiries bajas | Lead social, generalmente temprano en interacción | Media |

**Lectura recomendada:** P4/P5 sí contienen una dimensión conductual clara; P1/P2/P3/P6/P7 son principalmente segmentos de adquisición. En una siguiente versión conviene separar explícitamente **Acquisition Channel** de **Behavioral Maturity**.

## 3. Search Need — N1 a N3

| Cluster | N calibración | Share | Señales dominantes | Interpretación |
|---|---:|---:|---|---|
| **N1** | 1,135 | 46.3% | search_modality=rent 99% | **Necesidad de renta** |
| **N2** | 735 | 30.0% | search_modality=sale 100% | **Necesidad de compra/venta** |
| **N3** | 581 | 23.7% | both 83%; target_area mediana ~479 m² | **Necesidad flexible renta/venta**, con área objetivo mayor |

**Lectura recomendada:** Search Need funciona como estado de demanda, pero debe poder actualizarse en T1 porque la inquiry refina presupuesto y área.

## 4. Unified Spot — S1 a S7 — control de E006

| Cluster | N calibración | Share | Señales dominantes | Interpretación |
|---|---:|---:|---|---|
| **S1** | 504 | 27.3% | noroeste 30%; Yucatán/Mérida 19% | Cluster geográfico mixto; difícil de leer físicamente |
| **S2** | 277 | 15.0% | CDMX 100%; centro 100%; Cuauhtémoc 35% | **CDMX / centro** |
| **S3** | 259 | 14.0% | Bajío 100%; Querétaro 66% | **Bajío / Querétaro** |
| **S4** | 252 | 13.7% | floor_level mediana 15; elevators 9.5 | **Edificio vertical / piso alto** |
| **S5** | 191 | 10.4% | Nuevo León 100%; San Pedro 53% | **Nuevo León / San Pedro** |
| **S6** | 187 | 10.1% | Estado de México 99%; Naucalpan 54% | **Estado de México / Naucalpan** |
| **S7** | 175 | 9.5% | Jalisco 100%; Zapopan 52% | **Jalisco / Zapopan** |

**Conclusión:** 5 de 7 perfiles son esencialmente geográficos. S4 es la excepción física clara. Esto justifica conceptualmente separar PH + LOC.

## 5. Physical Space — PH1 a PH4

| Cluster | N calibración | Share | Señales | Nombre interpretable |
|---|---:|---:|---|---|
| **PH1** | 943 | 51.1% | Office 52%; Single 70%; renta 38%; luz natural 75%; área mediana 124.7 m² | **Espacio pequeño / office-like** |
| **PH2** | 488 | 26.4% | Industrial 100%; Single 72%; renta 42%; área mediana 2,841.9 m² | **Industrial grande** |
| **PH3** | 292 | 15.8% | Land 100%; Single 68%; área mediana 4,613.6 m² | **Terreno / land grande** |
| **PH4** | 122 | 6.6% | Office 48%; área mediana 2,248 m²; 3 charging ports; luz natural 81% | **Office/mixed grande con mayor equipamiento** |

- **PH1:** arquetipo dominante, mucho más pequeño que el resto y con mayoría relativa Office/Single.
- **PH2:** cluster físico muy limpio: 100% Industrial.
- **PH3:** 100% Land y mayor mediana de superficie.
- **PH4:** producto corporativo/mixed más grande y equipado.

**Calidad PH:** Gaussian Mixture K=4; min share 6.6%, max 51.1%, ARI 0.689.

## 6. Location — LOC1 a LOC7

| Cluster | N calibración | Share | Señales | Nombre interpretable |
|---|---:|---:|---|---|
| **LOC1** | 616 | 33.4% | centro 88%; CDMX 52%; Naucalpan/Lomas Verdes 19% | **Centro metropolitano CDMX–Naucalpan** |
| **LOC2** | 402 | 21.8% | Bajío 76%; Querétaro 50%; Juriquilla 27% | **Bajío / Querétaro** |
| **LOC3** | 222 | 12.0% | Nuevo León 100%; San Pedro 51% | **Nuevo León / San Pedro** |
| **LOC4** | 201 | 10.9% | Jalisco 100%; Zapopan 51%; Puerta de Hierro 51% | **Jalisco / Zapopan–Andares** |
| **LOC5** | 184 | 10.0% | noroeste 100%; Baja California/Tijuana 51% | **Noroeste / Tijuana** |
| **LOC6** | 112 | 6.1% | Chihuahua 100%; Centro 100% | **Chihuahua centro** |
| **LOC7** | 108 | 5.9% | Yucatán 100%; Mérida 100%; Paseo Montejo 100% | **Mérida / Paseo Montejo** |

**Calidad LOC:** K-Means K=7; min share 5.9%, max 33.4%, ARI **1.000**.

## 7. Broker — B1 a B7

Los Brokers se construyeron con historia anterior al cutoff. **Las señales de velocidad son low-trust** porque `broker_response_hours` no reconcilia limpiamente con `broker_response`.

| Cluster | N brokers | Share | Señales dominantes | Interpretación |
|---|---:|---:|---|---|
| **B1** | 66 | 22.0% | sale alto; centro alto; fast_rate bajo | **Centro + orientación a venta; respuesta relativamente menos rápida** |
| **B2** | 50 | 16.7% | centro alto; renta alta; median response ~7.1h | **Centro + renta; respuesta históricamente más rápida** |
| **B3** | 48 | 16.0% | noroeste, norte y occidente altos | **Broker geográficamente diversificado fuera del centro** |
| **B4** | 46 | 15.3% | precios renta/venta bajos; occidente alto | **Inventario de menor precio / value, sesgo occidente** |
| **B5** | 38 | 12.7% | centro-norte alto; renta alta; noreste bajo | **Centro-norte + renta** |
| **B6** | 31 | 10.3% | sureste y occidente altos; noreste bajo | **Especialización sureste/occidente** |
| **B7** | 21 | 7.0% | occidente alto; industrial y centro bajos | **Occidente no-industrial / nicho** |

## 8. Inquiry Intent — I1 a I7 — descartado

| Cluster | Señal dominante |
|---|---|
| I1 | Saturday 96% |
| I2 | Friday 100% |
| I3 | Monday 100% |
| I4 | Tuesday 100% |
| I5 | Sunday 100% |
| I6 | Thursday 100% |
| I7 | Wednesday 100% |

**Interpretación:** no representa intención comercial; representa día de semana. No se usa en E006/E007.

## 9. Mejores combinaciones de compatibilidad

Celdas calculadas sólo en future test, N>=50, con shrinkage hacia la tasa global de scheduled_visit (~20.77%) con prior strength 30.

| Rank | Combinación | N | Visit rate | Tasa suavizada | Lift | Interpretación |
|---:|---|---:|---:|---:|---:|---|
| 1 | **N2 × PH1 × B6** | 73 | 31.5% | 28.38% | **1.37x** | Compra/venta + espacio pequeño office-like + broker sureste/occidente |
| 2 | **N3 × PH1 × B5** | 81 | 29.6% | 27.24% | **1.31x** | Necesidad flexible + espacio pequeño office-like + broker centro-norte/renta |
| 3 | **N3 × LOC6** | 64 | 29.7% | 26.84% | **1.29x** | Necesidad flexible/área mayor + Chihuahua centro |
| 4 | **PH3 × B2** | 99 | 28.3% | 26.54% | **1.28x** | Terreno grande + broker centro/renta |
| 5 | **PH3 × B1** | 139 | 27.3% | 26.17% | **1.26x** | Terreno grande + broker centro/venta |
| 6 | **N2 × PH2 × B3** | 67 | 28.4% | 26.01% | **1.25x** | Compra/venta + industrial grande + broker regional diversificado |
| 7 | **PH2 × B3** | 184 | 25.5% | 24.87% | **1.20x** | Industrial grande + broker diversificado |
| 8 | **N2 × LOC2** | 258 | 24.8% | 24.39% | **1.17x** | Compra/venta + Bajío/Querétaro |
| 9 | **N1 × PH2 × B3** | 78 | 25.6% | 24.29% | **1.17x** | Renta + industrial grande + broker diversificado |
| 10 | **N3 × B5** | 132 | 25.0% | 24.22% | **1.17x** | Necesidad flexible + broker centro-norte/renta |

### Lectura de las celdas principales

- **N2 × PH1 × B6 — 1.37x:** mayor lift suavizado. Es una hipótesis de routing, no una regla. N=73 aún es limitado.
- **N3 × PH1 × B5 — 1.31x:** la flexibilidad del Lead puede importar más que un match rígido de área.
- **N3 × LOC6 — 1.29x:** señal local fuerte en Chihuahua centro; puede capturar composición de inventario/broker.
- **PH3 × B2 / B1 — 1.28x / 1.26x:** Land grande funciona con dos perfiles de broker distintos; sugiere una familia Physical×Broker más que una sola pareja idiosincrática.
- **N2 × PH2 × B3 — 1.25x:** combinación comercialmente muy interpretable: compra + industrial grande + broker regional diversificado.
- **N2 × LOC2 — 1.17x:** menor lift, pero N=258; es una de las celdas top con mejor soporte.

## 10. Qué NO debe hacerse

1. No convertir lift histórico en uplift causal.
2. No multiplicar automáticamente el score por 1.37, 1.31, etc.
3. No usar municipio/corredor como filtros rígidos.
4. No usar `broker_response_hours` como señal limpia de SLA.
5. No usar `spots.total_inquiries` como equivalente del conteo de `inquiries`.
6. No usar `market_context` históricamente hasta definir effective/publication time.
7. Mantener Availability con backward as-of; un join directo por `spot_id` expande ~10x las filas.

## 11. Evidencia fuente

- [EV-010](../Evidencias/EV-010_matching_ab_v3.md)
- [Interpretabilidad PH/LOC](results/spot_decomposition_interpretability.csv)
- [Interpretabilidad heredada P/N/S/B/I](../profile_clustering_v2/results/profile_interpretability.csv)
- [Celdas future test](results/compatibility_cells_future_test.csv)
- [Métricas A/B](results/model_metrics.csv)
- [Bootstrap](results/bootstrap_deltas.csv)
