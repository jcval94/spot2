# E015 — Offline baseline report

## Estado

**Fase 0–1 completas. LLM todavía no ejecutado.**

Este reporte no evalúa todavía si el LLM aporta valor. Establece la dificultad real del benchmark y el challenger determinístico que el LLM tendrá que superar.

## Copy extremadamente templated

Catálogo analizado: **3,000 spots**.

- descripciones exactas únicas: **856**;
- sólo **28.5%** de las filas tienen una descripción exacta única;
- **84.4%** de los spots comparten su descripción exacta con al menos otro spot;
- todo el catálogo utiliza únicamente **12 oraciones distintas** en `description`.

Esto es un hallazgo importante: un LLM no puede justificarse sólo por reconocer las frases actuales. Con únicamente 12 oraciones, un motor de reglas puede cubrir una proporción muy alta del lenguaje observado.

## Baseline Rules-only

Las cuatro familias iniciales son:

- iluminación natural;
- seguridad/control de acceso;
- estacionamiento;
- condición/readiness.

El baseline encontró **330 conflictos candidatos en 322 spots únicos (10.73% del inventario)**.

| Claim | Conflictos candidatos |
|---|---:|
| natural_light | 153 |
| readiness | 101 |
| security | 55 |
| parking | 21 |

314 spots tienen un único flag y 8 tienen dos.

Por sector:

| Sector | Spots | Flagged | Rate |
|---|---:|---:|---:|
| Industrial | 882 | 109 | 12.36% |
| Land | 497 | 67 | 13.48% |
| Office | 878 | 78 | 8.88% |
| Retail | 743 | 68 | 9.15% |

## Interpretación correcta

Estos 322 listings **no son 322 errores confirmados**.

Un conflicto entre copy y atributo sólo indica que:

1. las dos fuentes no son semánticamente consistentes bajo la regla;
2. debe revisarse cuál fuente es correcta;
3. la regla misma puede tener falsos positivos.

Por ejemplo, “recién remodelado” frente a `building_status=needs_renovation` es razonable como señal de revisión, pero menos incontrovertible que “buena iluminación natural” frente a `natural_light=false`.

## Gold set preparado

Se creó una muestra de **200 listings**:

- 25 Rules-positive y 25 Rules-negative por cada sector;
- selección determinística;
- campos para labels humanos;
- guía de etiquetado separada.

El gold set permanece sin etiquetas para evitar fingir revisión humana.

## Implicación para el LLM

El criterio de éxito se vuelve más exigente:

> El LLM debe encontrar issues accionables que estas reglas no detecten —por paráfrasis, combinaciones lingüísticas o relaciones semánticas menos triviales— manteniendo precisión alta.

Si no lo logra, la recomendación será **NOT_SUPPORTED: conservar Rules-only**.
