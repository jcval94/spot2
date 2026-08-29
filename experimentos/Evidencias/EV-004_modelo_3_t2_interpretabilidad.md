# EV-004 — Interpretabilidad T2

**Estado de evidencia:** empírica, permutation importance sobre test temporal + challenger Random Forest.

**Experimento:** [interpretabilidad_t2](../modelo_3/interpretabilidad_t2/)

## Evidencia fuente

- [Reporte](../modelo_3/interpretabilidad_t2/results/REPORT.md)
- [Fidelidad / comparación RF](../modelo_3/interpretabilidad_t2/results/model_fidelity.json)
- [Family importance](../modelo_3/interpretabilidad_t2/results/family_importance.csv)
- [Robustez primer/último T2 por lead](../modelo_3/interpretabilidad_t2/results/family_importance_robustness.csv)
- [Permutation multi-head](../modelo_3/interpretabilidad_t2/results/multihead_permutation_importance.csv)
- [RF permutation](../modelo_3/interpretabilidad_t2/results/rf_permutation_importance.csv)
- [RF impurity importance](../modelo_3/interpretabilidad_t2/results/rf_impurity_importance.csv)
- [Direccionalidad](../modelo_3/interpretabilidad_t2/results/directionality.csv)
- [Concordancia de rankings](../modelo_3/interpretabilidad_t2/results/rank_concordance.json)

## Resultados centrales

1. **Historial domina T2:** `interaction_history` pierde ΔAP +0.0638 y ΔAUC +0.0720 al permutarse.
2. **Robustez por lead:** sigue siendo la familia #1 en primer T2 (ΔAP +0.0471) y último T2 (ΔAP +0.0757).
3. **Challenger:** RF T2 logra AUC 0.609 / AP 0.524 / Lift@10% 1.43x frente a 0.595 / 0.515 / 1.39x del head T2.
4. **Inquiry actual condicionada a historia:** `current_inquiry` y `lead_spot_match` tienen importancia incremental promedio cercana a cero en todos los T2, aunque aumentan en el último T2.
5. **Proxy a auditar:** `availability_snapshot_age_days` aparece importante pero con dirección descriptiva contraintuitiva.
6. **Ranking inestable entre arquitecturas:** Spearman head-vs-RF 0.245 (permutation) y 0.259 (MDI).

## Caveats

- Importancia predictiva no es efecto causal.
- Variables correlacionadas pueden repartirse señal.
- El RF fue un challenger diagnóstico T2, no un benchmark exhaustivo de arquitecturas.
- El target es proxy `scheduled_visit` y los datos son sintéticos.

## Descubrimientos relacionados

- [D004](../conocimiento_agregado/DESCUBRIMIENTOS.md#d004--t2-obtiene-su-señal-principalmente-de-historia-observable)
- [D013](../conocimiento_agregado/DESCUBRIMIENTOS.md#d013--el-multi-head-todavía-no-gana-contra-especialistas-no-lineales)
- [D014](../conocimiento_agregado/DESCUBRIMIENTOS.md#d014--t2-captura-trayectoria-progreso-vs-estancamiento)
- [D015](../conocimiento_agregado/DESCUBRIMIENTOS.md#d015--la-última-inquiry-aporta-menos-que-la-trayectoria-acumulada)
- [D016](../conocimiento_agregado/DESCUBRIMIENTOS.md#d016--la-edad-del-snapshot-de-disponibilidad-requiere-auditoría)
- [D017](../conocimiento_agregado/DESCUBRIMIENTOS.md#d017--confiar-en-familias-no-en-el-ranking-exacto)
