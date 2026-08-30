# DRIFT_FINDINGS — development-only temporal cohorts

**Reference cohort:** 2025H1.  
**Comparison cohorts:** 2025H2, 2026Q1, 2026-Apr.  
**Calibration/holdout:** not inspected.

Metrics are stored in `outputs/eda/drift_metrics.csv`. Numeric drift uses reference-quantile PSI plus standardized mean difference (SMD); categorical mix uses Jensen–Shannon divergence; prevalence/missingness use absolute differences.

## Finding DRIFT-01 — Target prevalence is comparatively stable

- **claim:** No major target-prior collapse is visible inside development.
- **metric:** 2025H1 **19.94%**; 2025H2 **20.08%** (+0.14 pp); 2026Q1 **21.70%** (+1.76 pp); Apr-2026 **20.21%** (+0.27 pp).
- **population:** T1 DEVELOPMENT.
- **time_period:** 2025H1 → 2026-Apr.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** stable prevalence does not imply stable calibration conditional on features.

**Classification:** likely population/label mix is broadly stable; not the primary drift driver.

## Finding DRIFT-02 — Availability drift is a coverage regime change

- **claim:** Availability coverage is the dominant measured drift and should not be interpreted as LeadQuality population drift.
- **metric:** mean coverage 2025H1 **0.540** → 2025H2 **0.972** → 2026Q1 **0.9998** → Apr **1.000**. PSI vs 2025H1 is **7.85**, **12.52**, **12.52** respectively; SMD exceeds **2.1**.
- **population:** T1 candidate universe.
- **time_period:** 2025H1 → 2026-Apr.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** VERY_STRONG.
- **limitation:** source instrumentation/snapshot coverage is confounded with true inventory evolution.

**Classification:** **coverage change**, not automatically a real population change.

## Finding DRIFT-03 — Candidate depth grows strongly

- **claim:** The candidate policy exposes much deeper inventory later in time.
- **metric:** mean candidate count 2025H1 **21.97** → 2025H2 **36.03** → 2026Q1 **46.61** → Apr **51.19**. PSI: **0.90**, **1.87**, **3.07**; Apr SMD **1.44**.
- **population:** T1 candidate universe.
- **time_period:** 2025H1 → 2026-Apr.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** VERY_STRONG.
- **limitation:** candidate depth combines catalog growth and deterministic policy exposure.

**Classification:** **exposure/inventory change**. Keep outside LeadQuality core.

## Finding DRIFT-04 — Snapshot age changes after coverage saturates

- **claim:** Snapshot freshness is nonstationary and partly reflects snapshot-generation cadence.
- **metric:** median score-level snapshot age 23d (2025H1), 26d (2025H2), 18.5d (2026Q1), 17d (Apr). PSI vs reference rises above **1** and reaches **4.21** in Apr.
- **population:** T1 candidates with backward snapshots.
- **time_period:** 2025H1 → 2026-Apr.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** STRONG.
- **limitation:** conditional-on-coverage distributions change when missing snapshots disappear.

**Classification:** **coverage/snapshot-clock effect**.

## Finding DRIFT-05 — Total inquiry exposure declines toward the extraction boundary

- **claim:** Later leads have fewer total delivered inquiries, which is expected from less time to accumulate future interactions.
- **metric:** mean total inquiry exposure 4.97 (2025H1) → 4.48 → 4.37 → **3.92** (Apr); Apr SMD **-0.47**.
- **population:** T1 development leads, using full delivered future inquiry history for EDA only.
- **time_period:** 2025H1 → Apr-2026.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** VERY_STRONG_FOR_CLOCK_INTERPRETATION.
- **limitation:** this is intentionally post-score exposure and therefore cannot be a predictor.

**Classification:** **clock/progress effect**. Explicitly forbidden as T1 FE.

## Finding DRIFT-06 — Lead-to-first-inquiry lag has moderate clock/process drift

- **claim:** The observable T1 lag increases in later cohorts, but its temporal behavior is strong enough to require caution.
- **metric:** mean 10.75d (2025H1) → 17.82d → 21.78d → **30.43d** Apr; Apr PSI **0.19**, SMD **0.30**.
- **population:** T1 DEVELOPMENT.
- **time_period:** 2025H1 → Apr-2026.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** could encode acquisition/process clocks rather than durable intent.

**Classification:** **process/clock drift**. Keep AUDIT_ONLY/EXPERIMENTAL, not core.

## Finding DRIFT-07 — Core categorical mix is remarkably stable

- **claim:** Sector, modality, user_type, source and first-inquiry channel exhibit very small categorical distribution shifts.
- **metric:** Jensen–Shannon divergence versus 2025H1 remains below **0.0026** for every listed mix through Apr-2026.
- **population:** T1 DEVELOPMENT.
- **time_period:** 2025H1 → Apr-2026.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** STRONG.
- **limitation:** low marginal JS does not rule out interaction drift.

**Classification:** no evidence of large real categorical population shift.

## Finding DRIFT-08 — Missingness changes are small compared with Availability

- **claim:** Core lead/inquiry missingness moves only modestly.
- **metric:** urgency missingness reference 29.81%; latest 32.40% (+2.59 pp). Other audited missingness changes are generally within ~2.5 pp.
- **population:** T1 DEVELOPMENT.
- **time_period:** 2025H1 → Apr-2026.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** STRONG.
- **limitation:** structural modality missingness must be evaluated conditionally, not pooled.

**Classification:** mild missingness/collection drift.

## Synthetic-artifact caution

The delivered assessment dataset has several unusually clean/discrete design properties (fixed maximum interaction count, strongly ramping snapshot coverage, stable categorical mix). These may be synthetic-generation artifacts. No clock or coverage variable is promoted merely because it separates time cohorts.

## Drift policy consequence

- Monitor LeadQuality population drift separately from Inventory/coverage drift.
- Never use future exposure counts.
- Do not promote calendar time or extraction-progress proxies solely because they explain drift.
- Maintain explicit Availability coverage/freshness guardrails in Inventory.
- Report metrics by temporal cohort and key business segment after model selection.
