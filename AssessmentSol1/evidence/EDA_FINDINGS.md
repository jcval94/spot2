# EDA_FINDINGS — development-only, point-in-time aware

**Core model-facing scope:** T1 DEVELOPMENT only (`score_time < 2026-05-01 UTC`; N=4,368).  
**Original EDA selection authority:** DEVELOPMENT only.  
**Narrative exception:** Market Context may use the delivered extract for EDA-only business narrative because it is explicitly blocked from historical features.  
**Post-selection drift:** kept in a separate `POST_SELECTION_DRIFT_AUDIT.md`; it has no feature/model-selection authority.

This EDA is intentionally decision-oriented. It does not authorize a feature merely because an association exists.

## Finding EDA-01 — Demand is broad, with a relative Retail supply gap

- **claim:** Demand is distributed across all four sectors, but Retail is more represented in demand than in the historically existing Spot catalog at the development cutoff.
- **metric:** Retail demand share 30.40% vs supply share 24.51%; gap **+5.89 pp**; demand/supply share index **1.24x**. Office is almost balanced (29.35% vs 29.56%).
- **population:** 4,368 T1 development leads; 2,754 Spots created before 2026-05-01.
- **time_period:** 2025-01-01 through 2026-04-30 T1 scoring.
- **artifact:** `outputs/eda/demand_inventory_sector_gap.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** catalog share is not serviceability and does not account for price or historically mutable listing fields.

## Finding EDA-02 — T1 prevalence is stable enough to support temporal validation

- **claim:** The frozen T1 proxy does not exhibit the extreme temporal movement seen in Availability coverage.
- **metric:** Development prevalence **20.38%**. Monthly values range roughly 16.34%–23.73% in development; aggregated 2025H1=19.94%, 2025H2=20.08%, 2026Q1=21.70%, 2026-Apr=20.21%.
- **population:** mature T1 development rows.
- **time_period:** 2025-01 through 2026-04.
- **artifact:** `outputs/eda/monthly_t1_development.csv`, `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** `scheduled_visit` remains a proxy outcome, not final commercial conversion.

## Finding EDA-03 — asked_visit is valid intent, but not a magic leakage signal

- **claim:** `asked_visit` is known with the current inquiry and has a positive but modest unconditional association with the T1 target in development.
- **metric:** asked_visit=true: N=1,069, prevalence **21.33%**; false: N=3,299, prevalence **20.07%**; difference **+1.26 pp**.
- **population:** T1 DEVELOPMENT.
- **time_period:** through 2026-04-30.
- **artifact:** `outputs/eda/asked_visit_development.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** univariate association is not incremental model value or causal effect. The pre-registered WITH/WITHOUT sensitivity remains required.

## Finding EDA-04 — Area refinement is real and heavy-tailed

- **claim:** The first inquiry materially refines the intake need, justifying deterministic ratio/gap features rather than raw values alone.
- **metric:** intake target area median **395.05 m²**; first requested area median **480.9 m²**. Requested area p90 **2,561.1 m²** and max **40,920.9 m²**.
- **population:** T1 DEVELOPMENT.
- **time_period:** through 2026-04-30.
- **artifact:** `outputs/eda/numeric_summary.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** heavy tails are business-plausible; no trimming/winsorization is authorized globally.

## Finding EDA-05 — Urgency missingness is information, not zero urgency

- **claim:** Missing `urgency_days` is common enough that it must be represented explicitly as “not stated”.
- **metric:** missing rate **31.34%**; observed median **75 days**, p90 **296 days**.
- **population:** first inquiries in DEVELOPMENT.
- **time_period:** through 2026-04-30.
- **artifact:** `outputs/eda/numeric_summary.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** whether missingness itself predicts the target must be estimated only inside development folds.

## Finding EDA-06 — Future inquiry count is an exposure clock, not a T1 feature

- **claim:** Total inquiries per lead is useful to understand exposure but is not available at T1.
- **metric:** development extract mean **4.58**, median **5**, max **8** inquiries per lead.
- **population:** leads whose T1 lies in DEVELOPMENT.
- **time_period:** full delivered inquiry history observed after each T1.
- **artifact:** `outputs/eda/numeric_summary.csv`, `outputs/eda/monthly_t1_development.csv`.
- **evidence_strength:** STRONG_FOR_PROHIBITION.
- **limitation:** the metric intentionally looks forward for EDA exposure audit and must never enter the T1 feature matrix.

## Finding EDA-07 — Inventory coverage ramps dramatically over calendar time

- **claim:** Missing serviceability early in the sample is dominated by snapshot coverage rather than evidence that no inventory existed.
- **metric:** mean candidate-level backward Availability coverage is **83.93%** overall in development, but monthly coverage moves from **7.72% in Jan-2025** to **100% by Mar/Apr-2026**. Jan-2025 has a 59.04% “no known available candidate” rate; the rate becomes ~0% after early 2025.
- **population:** P4 candidate universe for T1 DEVELOPMENT.
- **time_period:** 2025-01 through 2026-04.
- **artifact:** `outputs/eda/monthly_t1_development.csv`, `outputs/eda/inventory_summary.csv`.
- **evidence_strength:** VERY_STRONG.
- **limitation:** “no serviceable” means no candidate with a known backward snapshot and `is_available=true`; UNKNOWN coverage is not unavailable.

## Finding EDA-08 — Candidate depth grows independently of LeadQuality

- **claim:** Candidate supply/exposure changes substantially while T1 prevalence stays comparatively stable, supporting the architectural separation of LeadQuality and Inventory.
- **metric:** median candidate depth grows from **16** in Jan-2025 to **49** in Apr-2026; development median is **29**.
- **population:** T1 DEVELOPMENT score × candidate policy.
- **time_period:** 2025-01 through 2026-04.
- **artifact:** `outputs/eda/monthly_t1_development.csv`, `outputs/eda/inventory_summary.csv`.
- **evidence_strength:** VERY_STRONG.
- **limitation:** candidate depth is policy-defined and should be evaluated as Inventory/Matching, not silently absorbed into core LeadQuality.

## Finding EDA-09 — Physical missingness is field-specific

- **claim:** Spot-attribute missingness must be represented by field and applicability rather than by blanket imputation.
- **metric:** charging_ports 20.2% missing; vertical_height_m 15.23%; floor_material 7.87%; several other physical fields have 0% missing.
- **population:** 3,000 raw `spot_attributes` rows.
- **time_period:** extract; attributes are authorized historically only under the frozen immutability assumption and Spot-existence gate.
- **artifact:** `outputs/eda/inventory_summary.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** no attribute-level timestamps exist; historical use depends on the explicit immutability contract.

## Finding EDA-10 — Raw Spot prices are useful narrative context only

- **claim:** Price distributions are highly skewed, but P4 does not have historical price versioning, so price compatibility cannot be promoted.
- **metric:** raw current/extract rent total median ~MXN 109.7k; sale total median ~MXN 19.3M; extreme tails are large.
- **population:** Spots existing before the development cutoff, evaluated using delivered extract values.
- **time_period:** extract/current-state price values.
- **artifact:** source audit plus EDA computation.
- **evidence_strength:** STRONG_FOR_REJECTION_AS_FEATURE.
- **limitation:** unversioned prices cannot be claimed as-of historical score_time.

## Finding EDA-11 — Market Context remains narrative-only

- **claim:** Market Context can explain business setting but cannot enter historical modeling.
- **metric:** source spans monthly aggregates, but no publication/effective timestamp exists.
- **population:** `market_context`.
- **time_period:** development-period narrative only.
- **artifact:** `evidence/DATA_AUDIT.md`.
- **evidence_strength:** VERY_STRONG_FOR_BLOCK.
- **limitation:** a month label is not an observation clock.

## Feature-engineering consequences

1. Keep core T1 focused on intake + current inquiry + deterministic T0→T1 refinement.
2. Pre-register asked_visit WITH/WITHOUT rather than deleting it or assuming dominance.
3. Treat urgency missing as “not stated”; do not replace with zero.
4. Build area and applicable-budget refinement deterministically.
5. Keep future exposure counts, Availability coverage, candidate depth, Spot attributes and selected-Spot context outside LeadQuality core.
6. Reject historical price compatibility under the current temporal contract.
7. Do not use Market Context or raw current-state Spot fields as model features.


## Pre-P8 assessment-alignment additions

### Finding EDA-12 — Proxy conversion differs descriptively by segment, but not enough to rescue T1 ranking

- **claim:** The frozen T1 scheduled-visit proxy has visible segment differences, especially by sector, but these are descriptive rather than evidence for segment-specific models.
- **metric:** Industrial **24.35%**, Land **21.07%**, Retail **19.35%**, Office **17.71%** in DEVELOPMENT. By channel, web **21.45%** vs phone **17.95%** (phone N=234).
- **population:** 4,368 mature T1 DEVELOPMENT leads.
- **time_period:** score_time < 2026-05-01.
- **artifact:** `outputs/eda/t1_proxy_rate_by_segment.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** this is the candidate-visible scheduled-visit proxy, not hidden commercial conversion; P7 showed no stable multivariable ranking lift.

This satisfies the business need to understand where observed proxy rates differ without creating post-result segment models.

### Finding EDA-13 — Market Context is useful for business narrative, not historical scoring

- **claim:** The supplied market table contains interpretable corridor/sector differences that help explain marketplace conditions.
- **metric:** among DEVELOPMENT-period descriptive highlights, Retail in `centro-chihuahua` averages ~**74 days** absorption; Retail in `del-valle-narvarte` ~**84 days**. Several Industrial corridor/sector cells show mean occupancy near **0.88–0.90** but slower mean absorption around **150–185 days**.
- **population:** `market_context` rows with `month < 2026-05-01`, aggregated by state × municipality × corridor × sector.
- **time_period:** DEVELOPMENT-period months only; narrative only.
- **artifact:** `outputs/eda/market_context_highlights.csv`.
- **evidence_strength:** MODERATE_DESCRIPTIVE.
- **limitation:** `month` is not a publication/effective timestamp; these aggregates remain EDA_ONLY and cannot enter historical modeling.

### Finding EDA-14 — Do not overclaim seasonality from the delivered horizon

- **claim:** Monthly T1 volume varies materially, but the sample is too short and confounded by process/coverage drift to justify a strong recurring-seasonality claim.
- **metric:** DEVELOPMENT first-inquiry counts range from **166** to **325** per month; first-inquiry lag and Inventory coverage also move strongly over calendar time.
- **population:** T1 DEVELOPMENT.
- **time_period:** 2025-01 through 2026-04.
- **artifact:** `outputs/eda/monthly_t1_development.csv`, `evidence/DRIFT_FINDINGS.md`.
- **evidence_strength:** STRONG_FOR_CAUTION.
- **limitation:** ~16 months and synthetic-generation/process effects are insufficient to identify a durable annual seasonal cycle.

The business conclusion is temporal nonstationarity, especially in Inventory/coverage, rather than a claimed seasonal law.
