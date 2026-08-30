# EV-033 — T1 semantic recovery

**Estado:** NOT_RECOVERED.

[E033](../feature_validation/E033_t1_semantic_recovery/)

La variante semantic_interactions seleccionada en validation fue evaluada una sola vez en E030 test.

Candidate:
- N **672**;
- prevalence **52.98%**;
- AUC **0.4637**, IC95% **[0.4213,0.5031]**;
- AP **0.5095**;
- AP/prevalence **0.962x**;
- Lift@10 **0.833x**.

Atomic baseline:
- AUC **0.4975**;
- AP **0.5245**;
- AP/prevalence **0.990x**;
- Lift@10 **0.944x**.

Delta candidate−atomic:
- ΔAUC **-0.0338**, IC95% **[-0.0664,-0.0022]**;
- ΔAP **-0.0150**, IC95% [-0.0447,+0.0099];
- ΔLift@10 **-0.111x**, IC95% [-0.328,+0.108].

El empeoramiento de AUC es robusto bajo bootstrap por lead. Dynamic Need/PH/LOC pueden seguir siendo útiles para interpretación/routing, pero esta combinación no debe promoverse a LeadQuality T1 bajo la target E028.

Fuente: [summary.json](../feature_validation/E033_t1_semantic_recovery/results/summary.json).


## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
