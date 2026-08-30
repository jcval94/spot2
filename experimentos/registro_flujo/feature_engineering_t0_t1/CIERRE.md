# Cierre

## Evaluación

**READY TO CLOSE.**

La línea de Feature Engineering T0/T1 ha alcanzado rendimientos decrecientes con el dataset actual y cuenta con suficiente evidencia negativa para tomar una decisión.

## Qué queda congelado

### Target

E028.

### ABT

E030.

### T0

- LeadQuality neutral evidence-backed.
- Search Need/specificity operativos/explicativos.

### T1

- LeadQuality neutral evidence-backed.
- Dynamic Need / PH / LOC / Lead×Spot fit para matching/routing experimental.

### T2

E029 candidate pendiente prospective gate.

## Qué NO está pendiente

No es necesario antes del cierre:

- probar más K;
- probar más interacciones de clusters;
- hacer tuning masivo;
- seguir target encoding sobre el mismo histórico;
- simular texto inexistente;
- reusar test E030.

## Qué pertenece a la siguiente fase

1. E029 prospective cohort.
2. E028 production A/A.
3. E039 si aparece raw inquiry text.
4. nuevas fuentes effective-dated.
5. target de cierre/lease real.

## Riesgos que deben seguir visibles

- drift temporal;
- target proxy ≠ cierre comercial;
- event time incompleto;
- Market Context sin effective time;
- current-state Spot fields inseguros históricamente;
- multiple testing en pockets de matching.

## Regla de reapertura

Una nueva iteración T0/T1 debe registrar qué **información nueva** introduce. Si no introduce información nueva ni una target/cohorte nueva, se considera continuación exploratoria no confirmatoria.

## Estado final

**CLOSED / DECISION-READY.**
