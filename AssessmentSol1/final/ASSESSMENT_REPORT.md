# Spot2 Lead Opportunity Assessment — Final Report

## Executive Summary

Spot2 needs a prioritization system that separates three questions that are related but not interchangeable:

1. **Lead Quality** — which first inquiries are more likely to reach the frozen outcome `scheduled_visit`?
2. **Inventory Serviceability** — can Spot2 serve the lead with point-in-time-known inventory?
3. **Lead Opportunity** — where do likely progression and current/fallback serviceability coincide?

The final clean-room system is frozen at **T1 (first inquiry)** and uses a small regularized Logistic Regression champion, `LQ_RECOVERY_R4_STATIC_MATCH_V1`. It recovered modest but directionally useful ranking signal without changing target or splits and without using Availability inside Lead Quality.

The operational score is **not** the historical E020 product and is **not** a jointly calibrated probability. Post-recovery analysis found double counting when continuous Inventory Serviceability was multiplied into a Lead Quality model that already contained selected-Spot matching context. The final score is therefore:

```
Opportunity Score V2
= lead_quality_probability × inventory_actionability_gate
```

The clean-room capacity policy is **P80 / top 20% within T1**. Fallback is capped at **K=3**, with `NO_RESULT` preferred over indefinite constraint relaxation.

The LLM requirement is satisfied through real semantic Inventory/Catalog QA work. The LLM remains a sampled discovery tool; neither LLM-derived features nor deterministic Semantic Rules enter final Lead Quality.

---

## 1. Business Problem

A lead can look commercially promising and still be impossible to serve with current inventory. Conversely, an inventory-perfect lead may have little evidence of progressing to the outcome.

The assessment therefore avoids collapsing these questions prematurely.

The production decision is conditional on the business objective:

- if Growth wants to maximize scheduled-visit progression regardless of inventory, prioritize by **Lead Quality**;
- if Growth wants progression **and** current/fallback serviceability, prioritize by **Lead Opportunity Score**.

That trade-off is a product decision, not a metric accident.

## 2. Scoring Moment

The final system scores at **T1: first inquiry**.

This is the first point where the system has:
- the lead;
- the first inquiry;
- the selected Spot;
- a defensible point-in-time information set.

The final target is:

`T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`

Question:

> Will this first inquiry eventually be recorded as `scheduled_visit`?

Maturity is frozen at 14 days. The target decision was made before model training.

Coverage is **4,953 / 5,000 = 99.06%**.

## 3. Temporal Design

Frozen split:

`SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30`

Primary partitions:

| Partition | N | Role |
|---|---:|---|
| Development | 4,368 | EDA, FE, temporal model selection |
| Calibration | 312 | calibration-only role |
| Procedural holdout | 290 | non-pristine diagnostic only |
| Post-holdout audit | 30 | partial-period audit |

Development model validation uses four expanding temporal folds with **2,390 total validation rows**.

The June holdout is permanently treated as **non-pristine / diagnostic-only** after a documented execution-export incident. It was not used for post-recovery model, score, fallback, or capacity selection.

## 4. Leakage Prevention

Final post-recovery audit status:

**READY — 0 active blockers.**

Key checks include:

- selected Spot future rows: **0 / 5,000**;
- OOF fold/role mismatches: **0**;
- OOF score-time mismatches: **0**;
- OOF target mismatches: **0**;
- product formula mismatches: **0 / 5,000**;
- forbidden outcome/internal-score columns in product output: **none**;
- fallback lists above K=3: **0**;
- procedural holdout used for post-recovery selection: **no**.

The final Lead Quality model does not use Availability, broker response, internal lead score, current mutable price, or future information.

## 5. Lead Quality Recovery

The initial Lead Quality state did not provide acceptable ranking signal, which triggered Prompt 11.5.

The recovery did **not**:
- change the target;
- change split boundaries;
- consume the June procedural holdout;
- introduce Availability;
- add outcome-derived features.

Final champion:

`LQ_RECOVERY_R4_STATIC_MATCH_V1`

Model:
- regularized Logistic Regression;
- RAW calibration.

Features:
1. `selected_spot_area_closeness`
2. `selected_spot_geographic_fit`
3. `selected_spot_attribute_completeness`

Recovery gate:

| Metric | Result |
|---|---:|
| Lift@10 | **1.0754x** |
| Lift@20 | **1.1146x** |
| AP | **0.2186** |
| Base-rate AP | 0.2083 |
| ROC AUC | 0.5134 |
| Lift@10 > 1 | **4/4 folds** |
| Lift@20 > 1 | **3/4 folds** |
| Lift@5 | **0.8593x** |

This is not a high-separation classifier. The value is concentrated in modest temporal ranking improvement at operational capacities.

The bootstrap uncertainty remains wide: ΔLift@10 CI95% is **[-0.2165, +0.2799]**. That limitation is intentionally visible.

## 6. Capacity Frontier

Capacity was re-evaluated using **DEVELOPMENT temporal OOF only**.

| Capacity | Lift | Recall | Precision |
|---:|---:|---:|---:|
| 5% | 0.859x | 4.4% | 18.0% |
| 10% | 1.075x | 10.8% | 22.4% |
| 15% | 1.084x | 16.4% | 22.5% |
| **20%** | **1.124x** | **22.6%** | **23.3%** |

Final policy:

**P80 / top 20% within T1.**

The top-5 slice remains below random and is not hidden. Top-20 was selected because it produced the strongest clean-room Lift among the passing 10/15/20 capacities while also maximizing recall.

Because score mass contains real ties, priority bands are rank-based rather than forced probability cutoffs.

## 7. Inventory Serviceability

Inventory is a separate point-in-time subsystem.

Availability uses backward as-of logic:

`latest snapshot_date <= score_time`

It does not use future `days_until_available` semantics to manufacture historical precision.

The system distinguishes states such as:
- AVAILABLE_NOW;
- AVAILABLE_WITHIN_URGENCY;
- UNAVAILABLE;
- UNKNOWN.

Current Spot prices are not historically versioned. Therefore precise historical budget fit is explicitly blocked/unknown rather than silently inferred.

## 8. Fallback

Fallback is intentionally short.

Post-recovery clean-room revalidation on DEVELOPMENT:

- any result: **4,361 / 4,368 = 99.84%**;
- at least 3 recommendations: **4,051 / 4,368 = 92.74%**;
- at least 5 recommendations: **3,696 / 4,368 = 84.62%**.

Final decision:

**K=3.**

The system prefers:
- known available inventory first;
- explicit `VERIFY_AVAILABILITY` when needed;
- `NO_RESULT` instead of unbounded relaxation.

Historical E020 also favored a short K, but the final K=3 is supported independently inside AssessmentSol1.

## 9. Lead Opportunity Score

Historical E020 established the useful conceptual idea that Lead Quality and Inventory should be integrated.

However, Prompt 11.5 changed Lead Quality itself: the recovered model already contains selected-Spot matching context.

A clean-room downstream re-evaluation showed that multiplying continuous Inventory Serviceability again created double counting.

At top 15%:

| System / objective | Lift |
|---|---:|
| Recovered Lead Quality → Lead Quality | **1.084x** |
| Raw `P_quality × InventoryServiceability` → Lead Quality | **0.977x** |
| Raw product → Joint Exact Serviceable | **1.244x** |

This is the central trade-off.

The raw product concentrated exact-serviceable joint positives, but it degraded pure Lead Quality ranking below random at that capacity.

Therefore the raw continuous product is **rejected diagnostic evidence**, not the production score.

Final formula:

```
Opportunity Score V2
= lead_quality_probability × inventory_actionability_gate
```

The continuous Inventory Serviceability score remains visible as a separate output.

### What the score means

The Opportunity Score is an **operational prioritization score**.

It is not:
- a calibrated probability of conversion;
- a calibrated joint probability of progression and availability;
- a causal estimate.

## 10. When to Use Quality vs Opportunity

### Use Lead Quality when

The operational objective is:

> maximize scheduled visits regardless of inventory.

### Use Opportunity Score when

The operational objective is:

> prioritize leads likely to progress and serviceable with current/fallback inventory.

This distinction should remain explicit in product requirements and monitoring.

## 11. Semantic Rules and Auxiliary Research

Final architecture classification:

- Matching / clusters: **AUXILIARY**
- Semantic Rules: **INVENTORY / CATALOG QA**
- Response-time Random Forest: **DIAGNOSTIC ONLY**

Semantic Rules are explicitly excluded from final Lead Quality scoring.

Historical E018 is supporting evidence only for this final decision. No post-hoc rule-subset search is permitted on the same historical OOF.

## 12. LLM / AI Use

The assessment used a real LLM where the dataset contained genuine unstructured language: listing copy.

Canonical E017 used `gpt-5-nano` with Structured Outputs on 100 real records:

- cost: **USD 0.002579**;
- new rule candidates: **0 / 100**;
- residual actionable: **0 / 100**.

The reusable semantic findings were converted into deterministic Rules-first checks.

AssessmentSol1 independently reproduces the deterministic sidecar over all 3,000 listings.

The final LLM role is therefore:

**sampled Semantic Inventory / Catalog QA discovery.**

The main Lead Opportunity Score has no runtime OpenAI dependency.

Human precision/recall is unavailable because no complete human-gold set exists.

## 13. Production Architecture

```
Lead + first inquiry + selected Spot
                │
                ├── Lead Quality
                │     Logistic Regression
                │     no Availability
                │
                ├── Inventory Serviceability
                │     PIT availability
                │     governed fallback K=3
                │
                └── Actionability gate
                       │
                       ▼
              Opportunity Score V2
                       │
                       ▼
               Rank-based capacity
                 P80 / top 20%
```

The LLM sidecar is outside the scoring critical path.

## 14. Monitoring and Scalability

Production monitoring should separate:

### Lead Quality
- score distribution;
- Lift/recall at operational capacities when labels mature;
- feature drift;
- calibration diagnostics;
- fold/cohort stability.

### Inventory
- point-in-time state coverage;
- stale snapshot rate;
- UNKNOWN / VERIFY_AVAILABILITY;
- fallback depth;
- NO_RESULT;
- recommendation constraint violations.

### Opportunity
- actionability rate;
- priority-band volumes;
- overlap between high Quality and serviceable leads;
- business outcomes after deployment without retroactively redefining the score.

A true prospective cohort is required for clean post-freeze confirmation.

## 15. Limitations

The final system intentionally retains the following limitations:

1. June procedural holdout is non-pristine and diagnostic-only.
2. Top-5 Lead Quality Lift is below 1.
3. Recovery uncertainty is wide.
4. Spot prices are unversioned historically, so budget-fit precision is blocked/unknown.
5. Score ties require rank-based priority bands.
6. No causal or commercial-conversion claim is supported.
7. Opportunity Score is not a jointly calibrated probability.
8. LLM human precision/recall is unavailable.

## 16. Final Decision

The clean-room supports a narrow production recommendation:

- score at T1;
- use the recovered Logistic Lead Quality model;
- expose Inventory as a separate serviceability subsystem;
- cap fallback at K=3;
- use Opportunity Score V2 for serviceability-aware prioritization;
- operate at P80/top20 as the frozen default;
- keep LLM and Semantic Rules outside the main scorer.

This architecture is intentionally simpler than several historical experiments because the final assessment retains only components that survived point-in-time, recovery and downstream consistency gates.
