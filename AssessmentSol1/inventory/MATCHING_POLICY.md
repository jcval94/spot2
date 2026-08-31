# Matching Policy

## Candidate universe

The builder starts from the score-time information set, not from observed conversion outcomes. It rejects future-created Spots before any ranking. Modality compatibility is mandatory.

Geographic relaxation is visible, not hidden in a scalar:

| Tier | Sector | Geography | Meaning |
|---|---|---|---|
| TIER_0 | same | preferred corridor | exact preferred market |
| TIER_1 | same | preferred municipality | municipality relaxation |
| TIER_2 | same | preferred state | state relaxation |
| TIER_3_EXPERIMENTAL | different | corridor/municipality/state | controlled sector relaxation; experimental |

Corridor and municipality are evaluated independently; the data dictionary explicitly says they are not a strict hierarchy.

## Area fit decision

Two deterministic alternatives were compared on DEVELOPMENT:

- Relative gap: `max(0, 1 - abs(candidate-requested)/requested)`.
- Log-ratio: `exp(-abs(log(candidate/requested)))`.

Across 567,869 DEVELOPMENT candidate pairs, mean absolute fit difference was 0.0811, median 0.00342 and Top-5 overlap was **94.85%**. The relative-gap form is frozen because it gives almost the same local ordering while making the business penalty directly interpretable. Viability requires relative area fit >= 0.50.

## Budget fit

Rent and sale are never mixed. The implemented pure function supports:

- rent: monthly lead budget vs historical monthly total rent;
- sale: total purchase budget vs historical total sale price.

Within budget yields fit 1. Above a ceiling receives an explicit monotonic ratio penalty. Intake intervals are used only when a current-inquiry requested budget is absent. Missing budgets stay missing.

However, the delivered Spot prices are unversioned current state. Canonical historical matching therefore **does not feed those prices into the function**. Current-price diagnostics were computed only to validate formula behavior; PIT-authorized price pairs remain zero. Canonical output is `budget_fit=null`, `budget_gap=null`, `UNKNOWN_PRICE_NOT_PIT`.

## Availability and confidence

Availability matching values are 1.0 now, 0.8 within expressed urgency, 0 unavailable and 0.4 unknown. The 0.4 is a matching placeholder, not a claim of probability. `inventory_confidence` is separately 1.0 (<=7d), 0.8 (<=30d), 0.55 (<=90d), 0.3 (>90d), 0 with no prior snapshot.

## Ranking alternatives

Only DEVELOPMENT was used.

**A — Tiered lexicographic**: tier first; within tier, availability state, viability, area fit, known budget fit if available, inventory confidence, then `spot_id`.

**B — Simple continuous challenger**: fixed, non-tuned weights area .25, budget .25, geography .20, sector .15, availability .15. Missing budget is omitted and remaining weights renormalized. No weight search was performed.

The policies had only **60.11% Top-5 overlap**. More importantly, the continuous challenger selected a relaxed tier as Top-1 despite an available Tier-0 candidate in **11.56%** of DEVELOPMENT scores, and selected Tier 3 despite same-sector inventory existing in **5.72%**. That conflicts with the product fallback hierarchy.

**Frozen decision: A, tiered lexicographic.** B remains audit-only. The choice is based on interpretability, coverage/stability and business consistency, not Lead Quality outcomes.
