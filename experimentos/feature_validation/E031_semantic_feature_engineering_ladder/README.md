# E031 — Semantic Feature Engineering ladder

## Objetivo

Separar el valor de la representación del valor del algoritmo. Se mantiene un Random Forest fijo y se añade Feature Engineering de forma acumulativa.

## Ladder

1. atomic — E030/E029 sanitized.
2. scale_specificity — logs, budget midpoint/width, search completeness, geography specificity, directional fit.
3. semantic_need — Search Need, requested modality, T0→T1 transition y semantic crosses.
4. soft_profiles — train-only Search Need / Dynamic Need / Physical / Location profiles + centroid distances.
5. semantic_interactions — profile interactions sin usar outcome-derived cell multipliers.

## Regla de selección

Sólo train/validation.

Una variante califica si validation cumple AUC >=0.52, AP/prevalence >=1.03 y Lift@10 >=1.05. Entre calificadas gana mayor AP/prevalence, luego Lift y AUC.

El test E030 no se usa hasta E032/E033.
