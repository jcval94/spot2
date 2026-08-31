# Research contamination

## Statement

The candidate dataset has already influenced substantial human/modeling decisions. Therefore no already-inspected candidate period may be described as a **pristine unseen holdout**.

Use **procedural final holdout** when a reserved historical slice is evaluated under a frozen protocol even though the broader dataset/time period has already informed research.

A procedural final holdout controls code/model tuning after freeze; it does **not** erase human research exposure.

## Known contamination paths

### Matching / segmentation

EV-010/EV-013 used a future test with:

- profile cutoff: 2025-09-29T12:58:37;
- future-test cutoff: 2026-04-28T07:41:43;
- 4,516 inquiries;
- 2,065 leads.

EV-013 explicitly records that this same future test was consumed for iterative discovery and cannot confirm newly discovered cells/hypotheses.

### Model architecture / trajectory

Modelo 3 and E005–E007 used single temporal holdouts and later rolling temporal CV. Those periods informed architecture, feature-family and trajectory conclusions.

### Drift / target / FE research

PR #9 E021–E040 repeatedly examined the candidate history to:

- diagnose temporal drift;
- ablate clocks/history/availability/broker priors;
- define the E028 target protocol;
- construct and sanity-check E029;
- construct E030;
- attempt T0/T1 feature recovery through E031–E037;
- freeze E038/E040 policy.

E029 itself states its historical rolling/calibration results are **post-selection diagnostics**, not confirmatory evidence.

### Semantic Rules / LLM

E015/E017 inspected listing-copy patterns and labeled/challenge samples. PR #20 E018 then tested deterministic semantic Rules on temporal OOF data. Re-searching subsets on those same OOF outcomes would be post-hoc multiple testing.

## Consequence for AssessmentSol1

1. Historical data can be used for development and methodological reconstruction.
2. Development splits still prevent row/lead leakage, but do not make the research process independent.
3. No claim of “unseen final performance” is allowed from an already-inspected period.
4. If a final historical slice is retained, call it a **procedural final holdout** and freeze target/features/models before opening it.
5. The strongest confirmation is a new post-freeze temporal cohort or Spot2's hidden evaluator/outcomes.
6. Once the procedural final holdout is opened, it is consumed. Any subsequent redesign makes it development evidence.

## Language to avoid

- “pristine holdout”
- “never seen before”
- “independent final test”

unless a genuinely new/hidden cohort satisfies that claim.
