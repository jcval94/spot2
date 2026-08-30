# Trazabilidad — Segmentación, perfiles y Matching

| Pregunta | Experimento / análisis | Evidencia | Descubrimientos | Decisión |
|---|---|---|---|---|
| ¿Perfiles balanceados y PIT-safe? | profile_clustering_v2 | EV-006 | D006, D009–D012 | clustering útil para representación |
| ¿Persona y Need son facetas distintas? | Persona + Search Need | EV-006 | D009 | Need se conserva; Persona con cautela |
| ¿Inquiry Intent es útil? | intent clustering | EV-006 | D010 | descartado |
| ¿Spot separa qué es vs dónde está? | E006 matching_ab_v3 | EV-010 | D011, D023 | Physical + Location |
| ¿Las tablas son seguras para matching? | relational audit | EV-010 | D025–D033 | as-of + exclusiones semánticas |
| ¿Flat interactions aportan? | E007 matching_ab_v3 | EV-010 | D024, D032 | benchmark global + pockets |
| ¿Persona puede limpiarse? | E008 | EV-013 | D038 | mejor semántica, no reemplazo |
| ¿Need cambia en T1? | E009/E012 | EV-013 | D039, D042, D048 | Dynamic Need challenger |
| ¿Broker Supply/Service? | E010/E013/E015 | EV-013 | D040, D043, D045 | Supply no; Service auxiliar |
| ¿Jerarquía supera flat? | E011/E016 | EV-013 | D041, D046, D049 | no ganador global nuevo |
| ¿Hay pocket prioritario? | cell analysis | EV-013 | D047 | DN4×LOC1×BSV1 |
| ¿Puede el mismo holdout confirmar más pockets? | cierre | EV-013 | D051 | no |
| ¿Qué arquitectura se congela? | consolidación | DECISION_SEGMENTACION.md | D052–D053 | decision-ready |

## Cadena principal

```text
profile_clustering_v2
        ↓
EV-006
        ↓
matching_ab_v3 + relational audit
        ↓
EV-010
        ↓
Physical + Location / E007 / PIT rules
        ↓
matching_profiles_v4
        ↓
E008 → E009 → E010/E011
        ↓
branch to strong baseline
        ↓
E012 → E013 FAIL → E015 → E016
        ↓
EV-013 / D038-D053
        ↓
DECISION_SEGMENTACION.md
```

## Artifacts fuente

- `experimentos/profile_clustering_v2/results/`
- `experimentos/matching_ab_v3/results/`
- `experimentos/matching_profiles_v4/results/`
- `experimentos/Evidencias/EV-006_profile_clustering_v2.md`
- `experimentos/Evidencias/EV-010_matching_ab_v3.md`
- `experimentos/Evidencias/EV-013_matching_profiles_v4.md`

## Runs autoritativos

- profile clustering v2: `33278286046`.
- matching A/B v3: `33281634395`.
- matching profiles v4: `33287168139`.
- v4 final reproducibility rerun: `33287533072`.

## Governance

- matching A/B: `33281634393`.
- v4: `33287168148`.
- final docs: `33287533051`.
