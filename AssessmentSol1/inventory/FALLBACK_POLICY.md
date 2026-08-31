# Fallback Policy

The fallback layer returns at most five deterministic recommendations. It never invents a Spot and never uses an LLM for reason text.

## Recommendation order

1. Apply the PIT candidate/existence gate and hard modality compatibility.
2. Require the frozen area viability threshold; if a future PIT budget fit is known, also require its frozen minimum.
3. Rank **known available** candidates lexicographically by tier and within-tier quality.
4. If no known-available candidate exists, return up to five viable `UNKNOWN` candidates with status `VERIFY_AVAILABILITY`.
5. Never recommend a candidate known to be unavailable.
6. Tier 3 remains visibly `TIER_3_EXPERIMENTAL` and cannot be described as equivalent to same-sector fallback.

Each recommendation includes `spot_id`, rank, tier, modality/sector match, area gap, budget gap, geographic match, availability state, snapshot age, confidence and deterministic reason codes.

## Reason codes

Canonical codes include `EXACT_PREFERRED_MARKET`, `MUNICIPALITY_RELAXATION`, `STATE_RELAXATION`, `EXPERIMENTAL_SECTOR_RELAXATION`, `AVAILABLE_NOW`, `AVAILABLE_WITHIN_URGENCY`, `VERIFY_AVAILABILITY`, area-fit state, freshness bucket, `UNKNOWN_PRICE_NOT_PIT` or `MISSING_BUDGET`.

## No-result behavior

- **No inventory / no PIT candidates:** no recommendation; `NO_INVENTORY`.
- **All known unavailable:** no recommendation; `ALL_UNAVAILABLE` unless viable unknown rows exist, in which case `VERIFY_AVAILABILITY`.
- **Availability unknown:** do not reinterpret as unavailable; return verification candidates only when no known-available option exists.
- **Budget impossible:** once a versioned PIT price exists, known budget fit below the frozen threshold can disqualify the candidate and produce `BUDGET_OR_AREA_IMPOSSIBLE`. In the current frozen data this state cannot be asserted because historical Spot price is not reconstructable.
- **No same-sector Spot:** Tier 3 may be surfaced only as experimental; never manufacture a same-sector fallback.
- **Only Tier 3 is serviceable:** recommendations are allowed only with `tier3_experimental_available=true` and `TIER3_ONLY_EXPERIMENTAL` status/reason.
- **Area impossible:** no recommendation when every candidate fails the frozen area threshold.

`fallback_available` means a known-available same-sector relaxation (Tier 1/2), not merely the existence of Tier 3.
