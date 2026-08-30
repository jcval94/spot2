# CALIBRATION_RULE_CORRECTION — CAL-001

**Type:** methodological inconsistency correction.  
**Performance-driven change:** NO.  
**Holdout reset:** NO — the procedural holdout remains consumed.

The frozen calibration rule states that RAW should win if learned calibration does not improve Brier/Log Loss materially. The first implementation accepted any numerically positive gain.

Observed CALIBRATION-only gains versus RAW were:

- Platt ΔBrier: **+0.00001946 improvement**
- Platt ΔLog Loss: **+0.00005969 improvement**
- Isotonic is effectively identical.

These changes are below the pre-registered **0.001 practical-tie tolerance** and are not material enough to justify a learned calibrator. Therefore the champion is corrected from **BASE_RATE + PLATT** to **BASE_RATE + RAW**.

Final T1 probability: **0.2037545788**, the DEVELOPMENT prevalence.

No target, split, feature set, model family or development result changes. No June holdout result was used to make this correction. The holdout remains `CONSUMED_BY_METHOD_INCIDENT_BEFORE_FREEZE`.
