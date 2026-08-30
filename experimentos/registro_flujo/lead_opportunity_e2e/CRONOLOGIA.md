# Cronología — FL-005

## 1. Lead Quality

Modelo 3 cerró pooled CatBoost + stage + trajectory como baseline operativo, con OOF temporal.

## 2. Matching / perfiles

La línea de segmentación cerró E007 como referencia de matching y demostró que availability debía ser point-in-time.

## 3. E019

Se congeló P85 en T1/T2 y se formalizó P(availability) a 30 días.

## 4. Gap restante

No existían todavía:

- fallback final;
- K elegido;
- fórmula de Lead Opportunity Score;
- evaluación conjunta.

## 5. E020

Se construyó una política bounded top-3 y se integró:

`P_quality × P_inventory_top3`.

El score combinado mejora sistemáticamente la concentración del proxy conjunto de oportunidad atendible, con un tradeoff explícito contra conversión pura.

La línea se cierra.
