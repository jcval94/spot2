# Spot2 Lead Opportunity — Executive One-Pager

## Decision

**Deploy a T1 first-inquiry prioritization system with two separate layers: Lead Quality and Inventory Serviceability. Use Opportunity Score V2 for serviceability-aware prioritization at P80/top20.**

### Final architecture

| Component | Final decision |
|---|---|
| Scoring moment | **T1 — first inquiry** |
| Target | first inquiry eventually recorded as `scheduled_visit` |
| Lead Quality | `LQ_RECOVERY_R4_STATIC_MATCH_V1` |
| Model | regularized Logistic Regression |
| Inventory | PIT backward-as-of serviceability |
| Fallback | **K=3** |
| Opportunity Score | `P_quality × inventory_actionability_gate` |
| Capacity | **P80 / top 20% within T1** |
| LLM | sampled Catalog/Inventory QA discovery only |

## Why this is the final system

The original Lead Quality state failed the prioritization gate. Recovery kept the target and temporal splits fixed and found modest but stable ranking signal without using Availability.

At the frozen capacity frontier:

- Lift@5: **0.859x**
- Lift@10: **1.075x**
- Lift@15: **1.084x**
- Lift@20: **1.124x**
- top20 recall: **22.6%**
- top20 precision: **23.3%**

Top20 is the default because it is the strongest passing clean-room capacity while retaining the most positives.

## The important trade-off

A rejected continuous product, `P_quality × InventoryServiceability`, improved concentration of exact-serviceable joint positives but hurt pure Lead Quality.

At top15:

- recovered Quality Lift: **1.084x**
- raw product Quality Lift: **0.977x**
- raw product joint-exact Lift: **1.244x**

So:

- **maximize scheduled visits regardless of inventory → Lead Quality**
- **prioritize progression + serviceability → Opportunity Score**

Opportunity Score is **not a jointly calibrated probability**.

## Inventory and fallback

Availability uses the latest snapshot known at score time.

Fallback is intentionally short:

- ≥3 recommendations: **92.74%** of DEVELOPMENT
- ≥5 recommendations: 84.62%

Final: **K=3**, with `NO_RESULT` before unbounded relaxation.

## AI / LLM

A real `gpt-5-nano` Structured-Output pilot cost **USD 0.002579** on 100 records.

It produced:
- 0/100 new-rule candidates;
- 0/100 residual actionable.

The useful semantic patterns became deterministic Rules-first checks.

**LLM remains a sampled Inventory/Catalog QA discovery tool and is not required to reproduce the score.**

## Governance

Post-recovery final audit:

**READY — 0 blockers**

Explicit limitations:
- June holdout non-pristine;
- top5 Lift < 1;
- wide recovery uncertainty;
- unversioned historical Spot prices;
- rank ties;
- no causal conversion claim;
- no joint probability claim.
