# Interpretabilidad T2 — Modelo 3

Este experimento busca responder una pregunta concreta:

> ¿Qué información explica que el head `T2_engaged` del Modelo 3 sea claramente más predictivo que T0/T1?

La carpeta es autocontenida y reutiliza únicamente el pipeline point-in-time de `experimentos/modelo_3`.

## Enfoque

Se usan tres lentes complementarias:

1. **Permutation importance directa sobre el head T2**  
   Se reentrena la arquitectura multi-head original con el mismo split temporal y se permuta una variable original a la vez en el conjunto de test T2. La caída de Average Precision y ROC-AUC mide cuánto depende el head de esa información.

2. **Random Forest T2 como modelo diagnóstico**  
   Se entrena un Random Forest sólo en snapshots T2. Se calculan:
   - permutation importance sobre variables originales;
   - impurity importance agregada desde las variables transformadas.

3. **Permutación conjunta por familias**  
   Se rompe simultáneamente la información de grupos completos:
   - perfil inicial del lead;
   - inquiry actual;
   - spot;
   - compatibilidad lead↔spot;
   - disponibilidad point-in-time;
   - historial acumulado;
   - flags de contexto.

La permutación conjunta conserva las relaciones internas del grupo usando la misma permutación de filas para todas sus columnas.

## Por qué no basta con impurity importance

La importancia interna de Random Forest puede favorecer variables continuas o de alta cardinalidad. Por eso la señal principal del análisis es la caída **out-of-sample y temporal** al destruir una variable, no el `feature_importances_` del árbol.

## Target y población

- Etapa: `T2_engaged` = segunda inquiry y posteriores, antes de una visita ya observada.
- Target: `scheduled_visit` futuro dentro de 30 días desde el timestamp de scoring.
- Split: el mismo 70/15/15 temporal por cohorte de lead del Modelo 3.
- Leakage: se heredan todos los controles point-in-time del pipeline original.

## Salidas

Después de ejecutar:

- `results/REPORT.md`: resumen ejecutivo y técnico.
- `results/model_fidelity.json`: comparación del head reentrenado y RF contra el resultado T2 original.
- `results/multihead_permutation_importance.csv`: importancia directa del head T2.
- `results/rf_permutation_importance.csv`: importancia por permutación del RF.
- `results/rf_impurity_importance.csv`: importancia MDI agregada por variable.
- `results/family_importance.csv`: caída al permutar familias completas.
- `results/directionality.csv`: perfiles descriptivos de las variables más importantes.
- `results/rank_concordance.json`: acuerdo entre métodos.
- `results/charts/*.png`: visualizaciones del ranking y las familias.

## Ejecución

```bash
pip install -r experimentos/modelo_3/interpretabilidad_t2/requirements.txt
python experimentos/modelo_3/interpretabilidad_t2/run_analysis.py
```

La interpretación es predictiva, no causal. Una variable importante indica que contiene información útil para ordenar leads T2; no demuestra que intervenir sobre ella aumente conversión.
