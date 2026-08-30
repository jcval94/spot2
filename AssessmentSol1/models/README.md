# Models — current status

## T1 — principal Lead Quality
Frozen champion: **BASE_RATE + RAW**, p=0.2037546.

No individual ranking capability.

## T0 — cold start
Decision: **NEUTRAL_EVIDENCE_BACKED**.

Intake-only Logistic does not beat Base Rate defensibly and the T0 target is strongly exposure-sensitive.

## T2 — re-scoring
Decision: **FUTURE_EXTENSION**.

The 33 strict-prior trajectory features add only +0.005 AP macro and fail the frozen complexity gate.

## Product implication

No stage currently supports a deployed predictive lead-ranking model:
- T0: no;
- T1: neutral probability prior only;
- T2: no.

The next modeling/business value must come from the independent Inventory Serviceability / Matching / Opportunity layer, not from further Lead Quality lift search.
