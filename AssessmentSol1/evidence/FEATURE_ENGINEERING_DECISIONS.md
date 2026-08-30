# FEATURE_ENGINEERING_DECISIONS — frozen before model training

**Target:** `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`  
**Split:** `SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30`  
**Procedural holdout opened:** **NO**

Each decision below is derived from the frozen temporal contract plus DEVELOPMENT-only EDA. No calibration or procedural-holdout result was used.

## FE-01 — Intake remains the T1 foundation

- **claim:** Lead intake fields are the only universally available cold-start context and remain the base feature family.
- **metric:** 4,368 DEVELOPMENT T1 leads span all sectors, modalities, user types, sources and geographies without major categorical drift (all audited JS divergence <0.0026 versus 2025H1).
- **population:** T1 DEVELOPMENT.
- **time_period:** 2025-01 through 2026-04.
- **artifact:** `outputs/eda/population_counts.csv`, `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** STRONG.
- **limitation:** stable marginal mix does not guarantee stable interactions.
- **decision:** raw intake + deterministic applicability/completeness transforms are REQUIRED/SUPPORTED in group A.

## FE-02 — Legacy prior counters remain blocked

- **claim:** `prior_searches`, `prior_inquiries` and `has_converted_before` cannot be promoted merely because their names imply historical information.
- **metric:** no event/observation clock proves the delivered aggregate was frozen at `leads.created_at`.
- **population:** all leads.
- **time_period:** historical backtest.
- **artifact:** `evidence/TEMPORAL_SEMANTICS.md`, `features/FEATURE_REGISTRY.csv`.
- **evidence_strength:** VERY_STRONG_FOR_BLOCK.
- **limitation:** production instrumentation could later make equivalent counters valid.
- **decision:** REJECTED / AUDIT_ONLY.

## FE-03 — Current inquiry is legitimate T1 information

- **claim:** channel, message length, requested area/budget, urgency and asked_visit are persisted with the inquiry before response.
- **metric:** first-inquiry payload has full message/area/channel/asked_visit coverage; urgency is unstated in 31.34%.
- **population:** T1 DEVELOPMENT.
- **time_period:** scoring instant at first inquiry.
- **artifact:** `outputs/eda/numeric_summary.csv`, P4 lineage.
- **evidence_strength:** VERY_STRONG.
- **limitation:** future response fields remain outcome-only.
- **decision:** group B REQUIRED; urgency missingness gets an explicit `urgency_not_stated` flag.

## FE-04 — asked_visit gets sensitivity, not special pleading

- **claim:** asked_visit is a valid contemporaneous intent signal, but its unconditional difference is modest rather than implausibly deterministic.
- **metric:** target prevalence 21.33% with asked_visit vs 20.07% without; +1.26 pp.
- **population:** T1 DEVELOPMENT.
- **time_period:** through 2026-04.
- **artifact:** `outputs/eda/asked_visit_development.csv`.
- **evidence_strength:** STRONG_DESCRIPTIVE.
- **limitation:** does not establish incremental value.
- **decision:** pre-register D_WITH_ASKED_VISIT vs D_WITHOUT_ASKED_VISIT. Never remove or promote based on intuition after results.

## FE-05 — T0→T1 refinement is deterministic and defensible

- **claim:** requested need at T1 meaningfully differs from intake and should be represented through stable arithmetic rather than learned bins.
- **metric:** intake target area median 395.05 m² vs first requested area median 480.9 m²; both are heavy-tailed.
- **population:** T1 DEVELOPMENT.
- **time_period:** score_time at first inquiry.
- **artifact:** `outputs/eda/numeric_summary.csv`.
- **evidence_strength:** STRONG.
- **limitation:** no current-inquiry geography field exists.
- **decision:** group C supports area ratios/gaps, applicable budget interval compatibility, modality consistency, completeness delta and need-change count. `geographic_refinement` is REJECTED in core because it would require selected-Spot geography.

## FE-06 — Structural missingness is not unknownness

- **claim:** budget nulls are often expected from modality.
- **metric:** raw audit shows rent/sale missingness aligned with modality; urgency missingness is instead genuinely “not stated”.
- **population:** lead/inquiry data.
- **time_period:** intake and current inquiry.
- **artifact:** `evidence/DATA_AUDIT.md`, `features/FEATURE_POLICY.md`.
- **evidence_strength:** VERY_STRONG.
- **limitation:** a future richer schema could distinguish additional missing states.
- **decision:** explicit `*_budget_applicable` and `*_budget_state` features; no global numeric fill that converts NOT_APPLICABLE into a pseudo-budget.

## FE-07 — T2 trajectory is reconstructed with a strict shift boundary

- **claim:** trajectory may add information after multiple interactions, but only request/event history strictly before the current inquiry is admissible.
- **metric:** no model result is used as evidence; D035 is inherited hypothesis only.
- **population:** T2 second+ inquiries.
- **time_period:** each current inquiry_at.
- **artifact:** `features/build_features.py`, `features/FEATURE_REGISTRY.csv`.
- **evidence_strength:** METHODOLOGICAL.
- **limitation:** incremental performance remains untested in AssessmentSol1.
- **decision:** materialize 33 deterministic trajectory features. Same-time batches see the same pre-batch history. No broker-response field is read by the trajectory builder.

## FE-08 — Inventory drift strengthens, not weakens, architectural separation

- **claim:** Availability coverage/candidate depth vary far more over time than core LeadQuality mix.
- **metric:** candidate depth mean 21.97→51.19 and Availability coverage 0.54→1.00 from 2025H1 to Apr-2026; target prevalence remains around 20%.
- **population:** T1 DEVELOPMENT.
- **time_period:** 2025H1 to Apr-2026.
- **artifact:** `outputs/eda/drift_metrics.csv`.
- **evidence_strength:** VERY_STRONG.
- **limitation:** inventory growth and instrumentation coverage are partially confounded.
- **decision:** Matching/Inventory stay outside core. Selected Spot context is allowed only in pre-registered Ablation E.

## FE-09 — Price compatibility is conceptually useful but temporally invalid here

- **claim:** budget-to-price compatibility would be a natural Matching feature, but historical Spot prices are unversioned.
- **metric:** raw delivered price distributions are strongly skewed; no effective timestamp exists.
- **population:** Spots.
- **time_period:** extract/current state.
- **artifact:** P4 forbidden policy; EDA narrative.
- **evidence_strength:** VERY_STRONG_FOR_REJECTION.
- **limitation:** price version history would change this decision.
- **decision:** `budget_to_price_compatibility` is REJECTED and not constructed.

## FE-10 — Clusters are optional profiles, not hidden model requirements

- **claim:** prior clustering work is insufficient reason to insert profile IDs into the canonical model.
- **metric:** historical evidence is used only as hypothesis; no AssessmentSol1 lift has been measured.
- **population:** development.
- **time_period:** future fold-specific fit if ever used.
- **artifact:** `features/FEATURE_POLICY.md`.
- **evidence_strength:** POLICY.
- **limitation:** profiles may still help interpretation/matching.
- **decision:** Search Need, Dynamic Need, Physical and Location are EXPERIMENTAL/AUDIT_ONLY and TRAIN-fold fit only. Broker Service is rejected this phase; Broker Supply and Inquiry Intent remain forbidden.

## FE-11 — E018 closes Semantic Rules for scoring

- **claim:** E018 did not pass its promotion gate.
- **metric:** macro ΔLift@10% = -0.0716; CI [-0.1438,+0.1251]; P(Δ>0)=45%; macro ΔAP +0.0019.
- **population:** historical E018 T1/T2 OOF diagnostic only.
- **time_period:** prior experiment.
- **artifact:** historical E018 report read-only; registry records decision.
- **evidence_strength:** STRONG_NEGATIVE_FOR_PROMOTION.
- **limitation:** E018 used a different historical experiment stack and is not AssessmentSol1 confirmation.
- **decision:** Semantic Rules = QA_ONLY; no semantic scoring ablation. No `llm_*` features.

## Frozen ablation consequence

Only the variants in `features/ablation_plan.json` may be evaluated for T1:

A. Lead intake only  
B. Lead + current inquiry  
C. + deterministic refinement  
D. WITH vs WITHOUT asked_visit  
E. selected-Spot-context challenger

No new variant may be introduced after results except to correct a documented implementation bug.
