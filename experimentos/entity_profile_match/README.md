# Experimento: perfiles Lead × Spot × Broker

Este experimento prueba si segmentar de forma no supervisada **Leads, Spots y Brokers** permite detectar combinaciones con una propensión de avance comercial distinta a la esperable por cada perfil individual.

El README se regenera automáticamente con resultados reales cuando corre `run_experiment.py`.

## Principios

- Clustering interpretable por entidad.
- Corte temporal para evitar leakage.
- Broker profile construido sólo con historia anterior al corte.
- `scheduled_visit` como proxy primario de avance; no se presenta como venta real.
- Comparación fuera de muestra entre efectos marginales e interacciones Lead×Spot×Broker.
- Resultados suavizados y con soporte mínimo para evitar "ganadores" por muestras pequeñas.

## Ejecución

```bash
python experimentos/entity_profile_match/run_experiment.py
```

GitHub Actions: `.github/workflows/entity-profile-match-experiment.yml`.
