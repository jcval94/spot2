# TARGET_OPTIONS — non-model bake-off

## Decision frame

This phase defines what **Lead Quality** means before feature engineering or model training. No model was trained and no AUC, AP, Lift, accuracy, or other predictive-performance statistic was computed or used.

The raw activity horizon used only for maturity/censoring is:

`max(inquiries.inquiry_at) = 2026-07-13T17:35:37Z`.

This is **not claimed to be the extraction timestamp**. The raw package has no extraction timestamp, so the latest inquiry event is used as a conservative observable-activity proxy.

## T1 scoring instant

For all T1 alternatives:

- score time = earliest `inquiry_at` for each `lead_id`;
- if timestamps tie, smaller `inquiry_id` is a deterministic tie-break;
- observed raw data contain **0 leads with a tied earliest inquiry_at**;
- scoring occurs after the inquiry has been persisted and before current broker response is known.

There are 5,000 leads and all have at least one inquiry.

---

## Target A — first-inquiry eventual outcome

### Estimand

> Probability that the **first inquiry itself** will eventually be recorded with `broker_response == "scheduled_visit"`.

The label is directly attached to the scoring inquiry.

Positive:
`first_inquiry.broker_response == "scheduled_visit"`.

Negative:
first inquiry has another non-null final status.

Missing response status:
**AMBIGUOUS**, never silently negative.

`broker_response_hours` is not needed and is ignored.

### Maturity bake-off

Maturity does **not** define the outcome horizon. It only determines whether an historical first inquiry is old enough to treat its delivered eventual status as reasonably mature.

| Buffer | Labeled | Censored | Cohort coverage | Prevalence |
|---|---:|---:|---:|---:|
| 7d | 4,994 | 6 | 99.88% | 20.364% |
| **14d** | **4,953** | **47** | **99.06%** | **20.351%** |
| 30d | 4,794 | 206 | 95.88% | 20.463% |

Across the 18 score months with at least 50 mature records under the 14-day rule:

- monthly prevalence SD: **1.66 pp**;
- monthly prevalence range: **7.40 pp**.

The prevalence moves by only **0.112 pp** across the 7/14/30 maturity choices.

### Strengths

- exact current inquiry → recorded outcome association;
- operational score time is unambiguous;
- no reconstructed response timestamp;
- 100% raw response-status population for first inquiries in the current package;
- almost complete mature cohort;
- label is easy to implement online/offline once the first-inquiry record reaches final status.

### Limitations

- not final commercial conversion;
- later successful inquiries do not retroactively make the first inquiry positive;
- the real resolution timestamp is absent for some responses;
- finality is approximated by maturity buffer because extraction time is absent.

---

## Target B — E028-style scheduled_visit within 30 days

### Estimand

> Probability that a **reconstructable scheduled_visit response event** occurs in `(score_time, score_time + 30d]`.

Candidate response event time:

`response_event_at = inquiry_at + broker_response_hours`.

Boundary:

`score_time < response_event_at <= score_time + 30d`.

A response exactly at score time is not future and is excluded. An event exactly at +30 days is included.

### Timing dependency

Raw `scheduled_visit` rows:

- total: **4,496**;
- with `broker_response_hours`: **3,823**;
- missing timing: **673**;
- timing coverage: **85.03%**.

The field is also globally semantically inconsistent: P1 found 3,786 `no_response` rows with numeric hours and 2,701 realized accepted/rejected/scheduled statuses without hours.

At the lead/T1 target level with a full 30-day observable window and no extra maturity:

- labeled: **4,555**;
- positive: **1,895**;
- negative: **2,660**;
- ambiguous: **239**;
- right-censored: **206**;
- labeled coverage: **91.10%**;
- observed prevalence: **41.60%**.

Monthly prevalence among adequately sized cohorts has:

- SD **7.70 pp**;
- range **29.09 pp**.

Additional maturity does not solve missing event time:

| Extra buffer beyond 30d | Labeled coverage | Ambiguous | Censored | Prevalence |
|---|---:|---:|---:|---:|
| 0d | 91.10% | 239 | 206 | 41.60% |
| 7d | 89.88% | 235 | 271 | 41.41% |
| 14d | 88.72% | 234 | 330 | 41.23% |
| 30d | 85.38% | 226 | 505 | 40.83% |

### Assessment

This target has attractive business semantics **if a true scheduled-visit event timestamp exists**. In this raw package it does not for all positives.

It is therefore not selected merely because it existed historically. The missing event-time problem is structural, not fixed by waiting longer.

---

## Target C — inquiry-initiation progress

### Frozen candidate definition

For T1 with `H = 30 days`:

> There exists an inquiry **initiated** in `[score_time, score_time + 30d]` that eventually has `broker_response == "scheduled_visit"`.

Crucially:

**This does not claim the visit was scheduled within 30 days.**

Only the successful inquiry initiation is bounded by 30 days.

This avoids inventing `response_event_at`.

### Maturity

Because an inquiry may be initiated near day 30 and its eventual status has no reliable event timestamp, maturity is applied **after the inquiry-initiation window**:

`score_time + 30d + maturity_buffer <= activity_horizon`.

| Post-window buffer | Labeled | Censored | Coverage | Prevalence |
|---|---:|---:|---:|---:|
| 7d | 4,729 | 271 | 94.58% | 44.343% |
| **14d** | **4,670** | **330** | **93.40%** | **44.197%** |
| 30d | 4,495 | 505 | 89.90% | 43.826% |

For 14d maturity, monthly prevalence SD is **6.91 pp** and range is **26.44 pp**.

### Assessment

C is **methodologically preferable to B** if the desired business estimand is “lead progress attributable to an inquiry initiated in the next 30 days,” because it does not fabricate response timing.

It is not preferred for the principal T1 Lead Quality score because a first inquiry can receive a positive label due entirely to a later inquiry. It therefore mixes the quality of the current inquiry with future lead behavior and future operational interactions.

---

## Maturity decision

For eventual-status targets, numeric timing provides a useful audit but is not used to define Target A.

Among 15,392 accepted/rejected/scheduled rows with numeric response hours:

- p50: 8.4 h;
- p95: 36.65 h;
- p99: 56.21 h;
- max: 108.9 h;
- 100% are <= 7 days.

Despite that, the untimed population prevents claiming that every response resolves inside 7 days.

**14 days is frozen** as the primary historical maturity buffer because:

1. it adds a conservative margin for untimed responses;
2. Target A prevalence is essentially unchanged versus 7 days;
3. coverage remains 99.06%;
4. 30 days loses materially more recent data without improving prevalence stability;
5. a two-week training-label latency is operationally realistic.

---

## Methodological ranking

| Criterion | A | B | C |
|---|---|---|---|
| Business meaning at T1 | **Direct current-inquiry outcome** | 30d future event | 30d lead progress |
| True event-time identifiable | Not required | **No** | Not required |
| Label/cohort coverage | **Very high** | Lowest | High |
| Ambiguity | **None observed** | 239 leads | None observed |
| Right censoring burden | **Low** | Medium | Medium |
| Prevalence stability | **Best** | Weakest | Weaker than A |
| Real-world implementation | **Simple** | Needs true response timestamp | Implementable, slower |
| Current inquiry causally/local semantically | **Strongest** | Mixed across inquiries | Weakest |
| Primary T1 choice | **YES** | NO | NO |
