# STAGE_POLICY — feature observability by stage

## T0

Only lead intake snapshot information. No inquiry, Spot, Availability, future exposure or outcome feature.

## T1 — principal

At `first inquiry_at`, after the request payload is persisted and before broker response is known:

- intake fields;
- current inquiry channel/message/area/budget/urgency/asked_visit;
- deterministic T0→T1 refinement.

Excluded from core: selected Spot, Spot physical attributes, Matching, Availability, future inquiry counts, Market Context, response fields and unproven intake counters.

## T2 — challenger

At each second-or-later inquiry:

- current request payload;
- strict-prior inquiry request/event trajectory.

Every historical aggregation is computed from state accumulated **before** the current event is appended. Same-time rows do not become history merely by inquiry_id ordering. No response-history feature is authorized.

## Matching / Inventory

Separate score × candidate block. Candidate Spot must exist by score_time; Availability uses backward as-of only. UNKNOWN remains UNKNOWN. Spot prices remain blocked by the frozen temporal contract.

## Fit boundary

Deterministic features may be materialized once from point-in-time inputs. Any learned transform/profile must be fit separately within each split TRAIN fold.
