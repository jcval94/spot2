# Decision log — Modelo 3

| Momento | Decisión | Evidencia disponible | Estado posterior |
|---|---|---|---|
| Inicio | No usar un único score estático; modelar T0/T1/T2 | E001 mostraba que interacción añade información | Se mantiene |
| E003 | Probar shared backbone + heads | Multi-Head > pooled NN | **Refinada** |
| E003 | Target futuro desde cada score_time, no desde creación del lead | necesidad de scoring dinámico point-in-time | Se mantiene |
| E003 | Aislar por lead y excluir post-conversion | control de leakage | Se mantiene |
| E004 | Priorizar historial observable en T2 | family permutation ΔAP ≈ +0.064 | Se mantiene |
| E004 | Interpretar T2 como progreso/estancamiento | robustez primer/último T2 | Se mantiene y E007 la valida predictivamente |
| E005 | No declarar ganador global con single holdout | IC95% macro AP cruzaba cero | Correcto; E006 resuelve la incertidumbre |
| E005 | T1 merece especialista fuerte | RF T1 mejora AP/AUC robustamente | Confirmado por E006 |
| E006 | Multi-Head deja de ser arquitectura líder | CatBoost/RF/pooled CatBoost > Multi-Head con CV | **Decisión final** |
| E006 | No implementar router por etapa todavía | selección cambia entre folds | Se mantiene |
| E007 | Incluir trajectory en pooled CatBoost | ΔAP T2 positivo con IC95% > 0 | **Decisión final** |
| E007 | No trasladar trajectory indiscriminadamente a RF | RF empeora significativamente | Se mantiene |
| Cierre | Baseline = pooled CatBoost + stage + trajectory | desempeño + simplicidad + estabilidad | **CLOSED / DECISION-READY** |

## Decisiones explícitamente descartadas

### “Multi-Head debe ser mejor porque cada etapa es distinta”

Descartada.

La heterogeneidad de etapa existe, pero un learner tabular pooled con `stage` puede representarla suficientemente bien y supera al Multi-Head actual.

### “Más heads/modelos siempre son mejores”

Descartada.

El híbrido tiene buen desempeño, pero su composición cambia entre folds; añade selección y complejidad sin estabilidad suficiente.

### “Trajectory mejora cualquier modelo”

Descartada.

Mejora pooled CatBoost y Multi-Head en T2, pero empeora RF.

### “Response time explica T2”

Descartada como narrativa causal/simple.

El historial importa, pero `broker_response_hours` no tiene semántica suficiente para defender un SLA causal y su efecto univariado no explica el resultado.

## Regla para reabrir esta decisión

Sólo reabrir la arquitectura si ocurre al menos uno:

1. una nueva cohorte temporal contradice E006;
2. aparece un outcome comercial mejor que `scheduled_visit`;
3. nueva información cambia materialmente el feature space;
4. una ablation/arquitectura nueva supera al baseline con comparación equivalente y evidencia robusta;
5. restricciones reales de producción cambian la función objetivo.
