# Leakage stress-test report

All stress tests are **NON_DEPLOYABLE** and live only in `AssessmentSol1/audit/stress/**`. They use the same frozen T1 DEVELOPMENT population: 4,368 leads, 890 observed proxy positives.

The purpose is not to improve the solution. It is to demonstrate how invalid information can change offline metrics and why the production harness must fail closed.

## Clean reference

The frozen Opportunity Score has:

- ROC AUC: **0.49781**
- Average Precision: **0.20230**
- Lift@10%: **0.977x**
- Recall@10%: **9.78%**

Because Lead Quality is constant, this is also the Inventory ranking.

## S001 — lead_score_internal

Tags: `LEAKAGE_EXPECTED / UNKNOWN_PROVENANCE / NON_DEPLOYABLE`.

The raw internal score has unknown generation time, inputs and possible target contamination.

Results:

- ROC AUC: **0.49880**
- AP: **0.20111**
- Lift@10%: **0.921x**

It does **not** improve the clean score. That is an important result: an unsafe variable is not justified merely because it exists, and leakage risk is independent of whether the leaked feature happens to look predictive in this sample.

## S002 — future inquiries

Tags: `FUTURE_LEAKAGE / NON_DEPLOYABLE`.

The rule was fixed before evaluation:

`future_inquiry_count + 2 × any_future_asked_visit`.

It deliberately uses inquiries with `inquiry_at > T1 score_time`, but does not need future `broker_response` to leak.

Coverage of the invalid future information:

- 3,872 / 4,368 DEVELOPMENT leads (**88.64%**) have at least one later inquiry;
- 2,484 (**56.87%**) have a later `asked_visit`;
- mean future inquiries per lead: **3.58**.

Results:

- ROC AUC: **0.51604** vs 0.49781 clean;
- AP: **0.21110** vs 0.20230;
- Lift@5%: **1.053x** vs 0.874x;
- Lift@10%: **1.011x** vs 0.977x;
- Lift@20%: **1.056x** vs 1.005x.

The apparent improvement is invalid because the information did not exist at the scoring instant.

## S003 — nearest Availability snapshot

Tags: `FUTURE_SNAPSHOT_LEAKAGE / NON_DEPLOYABLE`.

The only change is replacing the frozen backward-as-of rule with nearest snapshot by absolute date distance; ties deliberately prefer the later snapshot.

**52.31%** of Availability observations selected by this nearest rule are future snapshots relative to the lead score date.

Results:

- ROC AUC: **0.49989**
- AP: **0.20290**
- Lift@10%: **1.011x**
- Lift@20%: **1.028x**

Again, the metric can move upward while methodology becomes invalid.

## Governance

These results are forbidden from:

- Feature Engineering;
- feature selection;
- model selection;
- calibration;
- Inventory rule selection;
- Opportunity Score formula/threshold tuning.

The specs themselves carry `unsafe=true`, `deployable=false`, and explicit leakage tags. `audit/harness.py` rejects them in product mode.

`stress/run_stress_tests.py --allow-unsafe-stress --write` reconstructs the stress evidence directly from raw CSV using stdlib and imports no production scoring module.
