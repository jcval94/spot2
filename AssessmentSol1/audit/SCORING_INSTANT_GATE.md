# Scoring-instant information gate

Question: **What information is known at the exact scoring instant?**

The key distinction is between *known*, *model-eligible*, and *historically reconstructable*.

## T0 — lead creation

**Score time:** `leads.created_at`.

### Known at T0

Assuming the row is the intake snapshot captured at creation:

- `lead_id` as key;
- `user_type`, `company_size`, `industry`;
- `search_sector`, `search_modality`, `target_area_sqm`;
- modality-applicable rent/sale budget fields;
- `preferred_state`, `preferred_municipality`, `preferred_corridor`;
- `source`.

Historical counters (`prior_searches`, `prior_inquiries`, `has_converted_before`) are **conditional**: the raw row exposes them, but AssessmentSol1 still requires confirmation that they only summarize activity strictly before `created_at`. Prior evidence also places `prior_searches` in audit-only/blocked-for-LeadQuality status.

`lead_score_internal` may exist operationally but is **forbidden** because it is an internal score/leakage trap, not clean candidate information.

### Not known at T0

- current inquiry fields (no inquiry yet);
- current spot selected by inquiry;
- inquiry-specific Availability;
- current broker response;
- future target events;
- same-month Market Context unless publication/effective time is proven.

A market-wide inventory state could only be engineered later from spots that already existed plus backward-as-of availability; it is **not yet authorized** merely because the raw tables exist.

---

## T1 — first inquiry

**Score time:** the earliest `inquiries.inquiry_at` for the lead, with `inquiry_id` only as deterministic tie-break metadata.

### Known at T1

Everything safely known at T0, plus fields captured by the current inquiry:

- `spot_id` as join key;
- `channel`;
- `message_length`;
- `requested_area_sqm`;
- modality-applicable requested rent/sale budget;
- `urgency_days` (missing means not stated, not median urgency);
- `asked_visit`;
- current `inquiry_at`.

For the selected Spot:

- Spot exists only if `spots.created_at <= score_time`;
- descriptive fields/prices/location may be used only under an explicit immutability/versioning assumption;
- `spot_attributes` are conditional because they have no effective timestamp;
- raw `days_on_market`, `total_inquiries`, `total_views`, `is_active` are blocked as current-state leakage.

Availability:

- only the latest `availability_snapshot.snapshot_date <= score_time` for that `spot_id`;
- freshness is known as a diagnostic/guardrail;
- prior evidence treats >90-day snapshots as unknown for serviceability;
- never join to a future snapshot.

### Not known at T1

- `broker_response` of the current inquiry;
- `broker_response_hours` of the current inquiry;
- any derived response event from the current inquiry;
- any future scheduled visit.

Because T1 is the first inquiry, lead interaction-history features prior to this inquiry are structurally zero/empty except independently declared pre-lead history.

Calendar/progress values such as weekday/hour/days-from-lead-creation are **known**, but prior drift work makes them audit-only initially; “known” does not imply “safe propensity signal”.

---

## T2 — second or later inquiry

**Score time:** the current second-or-later `inquiry_at`, while no scheduled visit with a known event time has already occurred on/before score time.

### Known at T2

All current request/Spot/as-of-Availability information permitted at T1, plus **strictly prior** lead history:

- count of earlier inquiries;
- earlier unique Spots;
- earlier `asked_visit`, request, urgency and message-length summaries;
- prior response outcomes only when their response event is already realized at or before `score_time`;
- prior response-time summaries only over such realized events.

Current inquiry response is still future and blocked.

A previous inquiry whose response occurs after current T2 score time must **not** be counted as already realized.

Progress clocks (`inquiry_number`, `days_since_first_inquiry`, etc.) are observable but remain audit-only initially due the strong synthetic non-stationarity documented in E021/E022.

---

## Inventory — exact-time answer

At any score time `t`, defensibly known inventory is:

- Spots created on/before `t`;
- immutable/descriptive listing fields only if their historical mutability contract is confirmed;
- latest availability state per Spot from a snapshot dated on/before `t`.

Not defensibly known:

- extract-time/current mutable Spot fields as if they were historical;
- any availability snapshot after `t`;
- stale state silently carried forward as current truth;
- unversioned listing/attribute edits if mutability is possible.

Catalog semantic Rules/LLM audits describe listing quality; they are not automatically LeadQuality features.

---

## Broker response — exact-time answer

For the **current inquiry**, broker response and response hours are not known at scoring and are blocked.

For **prior inquiries**, response status may enter history only if a response event time can be established and `response_event_at <= score_time`.

Candidate data reconstructs `response_event_at` from `inquiry_at + broker_response_hours`, and prior evidence found missing/inconsistent timing. Therefore:

- unknown timing stays unknown;
- no-response with a numeric hour is not automatically a realized response;
- scheduled visits with unknown timing create target ambiguity;
- broker-level historical priors are not default LeadQuality features even when point-in-time computable.

---

## Market Context — exact-time answer

Current raw fields are keyed by `month`, but the repository does not establish when those monthly aggregates became known.

Therefore **Market Context is blocked at T0/T1/T2** until one of the following is proven:

- an effective/publication timestamp; or
- a business rule that allows a lagged, fully closed period to be reconstructed without future information.

A row with `month <= score_month` is not sufficient. Same-month occupancy, absorption, price or inquiry volume could include observations later than the scoring instant.

---

## Gate result

**PASS for PROMPT 0.** The information boundary is explicit for T0, T1, T2, inventory, broker response and market context.

This PASS authorizes the next raw-data semantics phase. It does **not** authorize target fitting, FE optimization, model training or final-test inspection.
