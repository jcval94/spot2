# Cronología — FL-004

## 1. Lead Quality temporal

Modelo 3 y E006/E007 establecieron que pooled CatBoost + stage + trajectory es el baseline operativo y dejaron OOF temporal suficiente para analizar capacidad.

## 2. Matching / availability point-in-time

EV-010/EV-013 demostraron que Availability debe reconstruirse backward-as-of y que no debe sustituirse por estado actual.

## 3. Gap operativo

Aunque existían Lift@10% y Recall@20%, no había una política final de capacidad ni un threshold congelado. Availability seguía entrando como categoría/estado, no como P(availability) explícita.

## 4. E019

E019 calculó la frontera 5/10/15/20/30% dentro de fold y stage, y construyó una probabilidad de disponibilidad a 30 días con validación temporal purgada.

Resultado:

- P85/top15 se adopta para T1/T2;
- T0 no activa priorización;
- P(availability) queda formalizada y validada.
