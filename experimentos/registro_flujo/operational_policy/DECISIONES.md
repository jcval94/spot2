# Decisiones — FL-004

## D1 — No usar un raw threshold global

**Estado:** CURRENT.

Razón: los cutoffs equivalentes cambian materialmente entre folds. Se adopta percentile threshold por etapa.

## D2 — No forzar threshold de priorización en T0

**Estado:** CURRENT.

Razón: Lift se mantiene alrededor de 1.0. T0 conserva score informativo, no una cola high-priority.

## D3 — P85/top 15% en T1/T2

**Estado:** CURRENT.

Razón: preserva prácticamente el lift de top10 mientras aumenta el recall ~49–50% relativo.

## D4 — No convertir days_until_available en una curva manual

**Estado:** CURRENT.

Razón: la tasa futura observada es casi plana entre buckets. Una curva monotónica fabricaría precisión no soportada.

## D5 — P(availability) con current state + transición histórica por sector

**Estado:** CURRENT.

Razón: es calibrable, point-in-time, simple y evita introducir features sin señal probada.

## D6 — Agregación lead-level por máximo

**Estado:** CURRENT.

Razón: responde a “¿existe al menos una opción viable?” sin asumir independencia entre listings.
