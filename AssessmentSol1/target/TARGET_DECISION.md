# TARGET_DECISION — frozen before feature engineering

## Decision

The principal Lead Quality target is frozen as:

**`T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`**

with **14-day historical maturity**.

No model was trained to make this decision. No AUC, AP or Lift was computed or consulted.

## Exact product question

> **Will this first inquiry eventually be recorded as `scheduled_visit`?**

This is intentionally narrower than “will the lead eventually convert?” and narrower than “will the lead obtain a visit on any inquiry within 30 days?”

That narrowness is a strength for the T1 product: the score is attached to the exact inquiry that has just arrived.

## Why A wins

### 1. Semantics

The first-inquiry outcome is the closest available label to the immediate T1 decision.

The score is produced for an inquiry and the label belongs to that same inquiry.

### 2. Temporal identifiability

A needs no invented response timestamp.

Target B requires `broker_response_hours` to assert that a scheduled-visit event occurred inside 30 days, but 673/4,496 scheduled_visit rows lack those hours.

Target C avoids this timestamp problem but changes the estimand to future lead progress across later inquiries.

### 3. Coverage

At the frozen 14-day maturity rule:

- A: **4,953 / 5,000 = 99.06%**
- B30, no extra maturity: **4,555 / 5,000 = 91.10% labeled**
- C30 +14d: **4,670 / 5,000 = 93.40%**

### 4. Ambiguity and censoring

A14:

- ambiguous: **0**
- maturity-censored: **47**

B30:

- ambiguous: **239**
- right-censored: **206**

C30/14:

- ambiguous: **0**
- censored: **330**

### 5. Prevalence stability

This criterion is permitted because it evaluates label behavior, not model predictability.

For adequately sized monthly cohorts:

- A14 monthly SD: **1.66 pp**, range **7.40 pp**
- B30 monthly SD: **7.70 pp**, range **29.09 pp**
- C30/14 monthly SD: **6.91 pp**, range **26.44 pp**

This does not prove A is “more predictable.” It shows the definition itself is substantially less time-variant in the delivered raw package.

## Why not B

B has a good conceptual business horizon but poor event-time identifiability.

It should be reconsidered only if Spot2 exposes a true immutable `response_event_at` or `scheduled_visit_at`.

Waiting 7/14/30 extra days does not manufacture the missing timestamp.

## Why not C as principal T1

C is useful and cleaner than B for 30-day lead progress.

However, a first inquiry can be labeled positive because a different inquiry 20 days later succeeds. That is a different product question.

C is therefore retained as a **secondary progress estimand**, not discarded.

## Frozen maturity = 14 days

Seven days is empirically plausible because every realized response with numeric timing in the raw package is <=108.9 hours. But the missing-timing subset prevents proving that rule universally.

Fourteen days is selected as a conservative compromise:

- only 47 T1 leads are excluded;
- prevalence is essentially unchanged from 7d;
- it provides additional protection against late finalization;
- 30d costs substantially more coverage without a stability benefit.

Again, the 14 days are **maturity**, not the outcome horizon.

## Secondary stage contracts

### T0

Frozen secondary target:

**`T0_30D_INQUIRY_INITIATION_PROGRESS_V1`**

Question:

> From lead creation, will the lead initiate at least one inquiry during the next 30 days that eventually gets recorded as scheduled_visit?

Use 30-day inquiry-initiation horizon + 14-day maturity.

Current audit:

- eligible: 4,710;
- positive: 1,957;
- prevalence: 41.55%.

This is **not the same estimand** as T1 A.

### T2

Outcome semantics are frozen as:

**`T2_CURRENT_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`**

but the historical training cohort is **not yet authorized**.

T2 stage membership requires knowing that no prior scheduled visit was already realized at the current score time. Missing prior response timing makes some of that historical membership ambiguous.

The P4 point-in-time ABT gate must resolve/exclude those rows before a T2 training cohort exists.

Even though T2 uses the same current-inquiry outcome definition as T1 A, it conditions on a different population (leads that progressed to T2). Its probability therefore is **not the same estimand** as the T1 probability.

## Freeze rule

From this commit onward:

**A future model producing better Lift/AUC/AP under another label is not a valid reason to change this target.**

A target change requires a new contract version and a non-model methodological bake-off triggered by business/source semantics, new authoritative instrumentation, or a discovered labeling defect.
