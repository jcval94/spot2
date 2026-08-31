# Final methodological leakage audit

## Overall verdict

**READY — zero active BLOCKERS.**

This means the frozen T1 product pipeline is methodologically coherent enough to package under its explicit limitations. It does **not** mean performance is strong, causality is established, the historical holdout is independent, or every source has perfect observation-time provenance.

## Pipeline audit

### RAW DATA

Raw CSV/Parquet are alternate representations, not concatenated sources. Outcome/current-state bait fields are identified in temporal registries.

`lead_score_internal` is forbidden from the clean system. Current-state Spot fields, unversioned prices, Market Context and `competing_inquiries_30d` are blocked from historical prediction where provenance is insufficient.

### Temporal semantics

The clean pipeline separates event, observation, effective and extraction/current-state time.

T2 inquiry aggregates use only strict-prior events. Candidate Spots require creation by score time. Availability is backward-as-of only. Same-day Availability remains conditional on a business-date assumption because no ingestion timestamp exists.

### Target and maturity

The primary target is first-inquiry eventual `scheduled_visit`, not commercial conversion.

`broker_response` is label-only. `broker_response_hours` is not a predictive feature.

The 14-day maturity policy is **LABEL_MATURITY_ASSUMED**, not an observed label-publication timestamp. The raw package lacks extraction time, so the maximum inquiry timestamp is a conservative observation-horizon proxy.

### Splits and entity isolation

The split contract is calendar based. Each T1 lead has one partition row. Fold training and validation lead sets are explicitly checked for intersection and temporal order. ABT validators reject duplicate grain and cross-partition entity leakage.

### Score spine / ABTs

T1 has one deterministic first-inquiry row per lead. T2 has one row per second-or-later inquiry and strict-prior history. P3 ABTs are explicitly superseded and forbidden downstream; the P4 raw-equivalence authority is the relevant contract.

### Feature Engineering

Core T1 deterministic features use score-time inputs only.

Learned preprocessing is guarded: median imputation, StandardScaler and OneHotEncoder fit only after an all-TRAIN role assertion. Optional KMeans has the same guard and is not part of the frozen core. No target encoding or frequency encoding is used in the final core.

Selected-Spot context exists only as pre-registered Ablation E and is challenger-only.

### Model

Model/feature-family selection uses DEVELOPMENT folds. The final champion is `BASE_RATE + RAW`, no features. This substantially reduces final predictor leakage surface.

### Calibration

Calibrator comparison/selection is internal to CALIBRATION. The final corrected calibrator is RAW. The procedural holdout is not used to select calibration.

### Inventory / fallback

Inventory is deterministic and separate from Lead Quality. It rejects future Spots, future snapshots, unversioned price history and unproven competing-inquiry windows. Fallback returns deterministic, explicitly tiered candidates and preserves UNKNOWN availability.

### Opportunity Score

The frozen score is `P(LeadQuality) × InventoryServiceability`. Clean Lead Quality has no Spot/Inventory inputs; double-counting audit therefore passes.

Because Lead Quality is constant, the final ranking is Inventory ranking. The assessment correctly avoids claiming incremental ranking power from the multiplication.

### Metrics / research contamination

DEVELOPMENT metrics are development evidence.

The June period was already consumed by a documented method incident before final freeze and remains `PROCEDURAL_HOLDOUT_DIAGNOSTIC_ONLY`. No claim of pristine/unseen/independent confirmation is allowed.

## Findings by severity

### BLOCKER

**None active.**

### MATERIAL

1. **Research contamination / holdout incident.** June cannot support independent-confirmation claims. It is contained because it is diagnostic-only and did not drive frozen decisions.
2. **Exact canonical Polars execution unavailable in the active review runtime.** Raw-equivalence evidence and static code review are strong, but the exact project build/tests should be run in the intended environment before external handoff.
3. **T2 historical stage eligibility is only partially observable.** Timed prior scheduled visits use reconstructed response timing; untimed prior visits become ambiguous. T2 is already classified FUTURE_EXTENSION and is not the deployed T1 product.

### MINOR

1. Product `data_fingerprint` directly lists CSV leaf SHAs even though canonical readers prefer Parquet. The included raw-source-manifest SHA pins both CSV and Parquet representations, so score provenance is still recoverable; use direct canonical-Parquet leaves in the next metadata version.
2. Superseded P3 builders remain visible for chronology. Authority files clearly forbid them downstream.
3. The root AssessmentSol1 README has historical phase wording from Prompt 8; authoritative component READMEs/configs are newer.

### ACCEPTED_LIMITATION

- label maturity observation horizon is assumed from available raw activity;
- Availability is business-date, not proven intraday observation time;
- Spot structural fields and `spot_attributes` rely on explicit invariance assumptions where raw field-level timestamps are absent;
- unversioned Spot prices cannot support historical budget fit;
- June is procedural/non-pristine;
- current Opportunity ranking has no demonstrated positive-outcome enrichment.

## Stress-test conclusion

S001 demonstrates that unknown provenance is unacceptable even when it does not improve metrics.

S002 demonstrates that later inquiry information can make offline metrics look better.

S003 demonstrates that nearest-snapshot joining selects future information at material frequency and can also improve offline ranking metrics.

None of these results changed the clean pipeline.

## Gate

`final_audit.json` may declare READY because active BLOCKER count is zero.

READY should be read as **methodologically ready under explicit limitations**, not as “validated business impact.”
