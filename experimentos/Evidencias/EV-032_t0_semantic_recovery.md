# EV-032 — T0 semantic recovery

**Estado:** NOT_RECOVERED.

[E032](../feature_validation/E032_t0_semantic_recovery/)

La variante soft_profiles elegida exclusivamente en validation fue evaluada una sola vez en E030 test.

Candidate:
- N **698**;
- prevalence **52.01%**;
- AUC **0.4897**, IC95% **[0.4501, 0.5300]**;
- AP **0.5016**;
- AP/prevalence **0.964x**;
- Lift@10 **0.824x**.

Atomic baseline:
- AUC **0.4892**;
- AP **0.5002**;
- Lift@10 **0.797x**.

Delta candidate−atomic:
- ΔAUC **+0.0005**, IC95% [-0.0362,+0.0353];
- ΔAP **+0.0013**, IC95% [-0.0245,+0.0256];
- ΔLift@10 **+0.027x**, IC95% [-0.162,+0.319].

No existe evidencia de recovery T0 con esta primera familia semántica.

Fuente: [summary.json](../feature_validation/E032_t0_semantic_recovery/results/summary.json).


## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
