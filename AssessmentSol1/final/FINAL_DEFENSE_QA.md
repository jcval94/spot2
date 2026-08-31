# Final Methodology Defense — Q&A

## Why this final scoring moment?

**T1 / first inquiry** is the first operational moment with lead context, inquiry context and a selected Spot while still preserving a defensible pre-outcome information set.

It also aligns directly with the frozen target: the outcome belongs to the same first inquiry being scored.

## Why this target?

`T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` asks whether the first inquiry is eventually recorded as `scheduled_visit`.

It was selected before modeling because:
- event semantics are directly attached to the scored inquiry;
- it avoids inventing missing response timestamps;
- 14-day maturity provides 99.06% coverage;
- label prevalence is materially more stable than the tested 30-day alternatives.

## Why this Lead Quality architecture?

The architecture keeps progression propensity separate from Inventory serviceability.

That separation prevents the Lead Quality head from becoming an implicit availability model and makes the final business trade-off explicit.

## Why Logistic Regression rather than the earlier models/baselines?

The final champion is not selected because Logistic Regression is universally superior.

Prompt 11.5 found that the smallest regularized Logistic ranker using three selected-Spot structural match features satisfied the recovery ranking gate with less unnecessary complexity than the interaction challenger.

The previous Base Rate state is superseded as the final champion.

## What changed during Lift recovery?

The target, maturity and temporal splits did not change.

The recovery identified a small amount of defensible selected-Spot structural signal:
- area closeness;
- geographic fit;
- attribute completeness.

Availability remained excluded.

## Why is the recovered model not leakage?

The final post-recovery audit verifies:
- selected Spot exists by score time for all 5,000 scored leads;
- zero OOF fold-role mismatches;
- zero OOF score-time mismatches;
- zero OOF target mismatches;
- no Availability, response, internal score or future price state in Lead Quality;
- June procedural holdout was not used for recovery selection.

## How strong is the recovered signal?

Modest.

Recovery evidence:
- Lift@10 ≈ 1.075x;
- Lift@20 ≈ 1.115x;
- AP ≈ 0.2186 vs base-rate AP ≈ 0.2083;
- Lift@10 > 1 in 4/4 temporal folds.

Weaknesses:
- Lift@5 ≈ 0.859x;
- ROC AUC ≈ 0.513;
- bootstrap uncertainty is wide.

This supports operational ranking, not a claim of strong individual-level classification.

## Why P80 / top20?

Capacity was reevaluated post-recovery on DEVELOPMENT temporal OOF:

- 5%: Lift 0.859x;
- 10%: 1.075x;
- 15%: 1.084x;
- 20%: 1.124x.

Top20 is the strongest passing clean-room capacity among 10/15/20 while maximizing recall at 22.6%.

Historical E019 P85/top15 is supporting evidence only.

## Why K=3 fallback?

AssessmentSol1 independently revalidated fallback list completion on DEVELOPMENT:

- ≥3 results: 92.74%;
- ≥5 results: 84.62%.

K=3 provides a short operational list without requiring indefinite relaxation. `NO_RESULT` remains allowed.

## Why combine Quality and Inventory?

Because a high-propensity lead can still be operationally impossible to serve.

Lead Quality answers progression propensity; Inventory answers serviceability. Opportunity Score is useful when the operating objective requires both.

## Why not multiply continuous Quality × Inventory Serviceability?

After recovery, Lead Quality already contains selected-Spot matching context.

At top15:
- recovered Quality → Quality Lift: 1.084x;
- raw continuous product → Quality Lift: 0.977x;
- raw product → joint-exact Lift: 1.244x.

The product concentrated serviceable joint positives but damaged pure Lead Quality ranking. That is evidence of the trade-off and of repeated match-strength weighting.

## Why use an actionability gate in V2?

V2 keeps a minimal operational feasibility constraint inside the priority score without multiplying continuous match strength twice.

`Opportunity Score V2 = lead_quality_probability * inventory_actionability_gate`

Continuous Inventory Serviceability remains a separate output.

## Why is Opportunity Score not a jointly calibrated probability?

The system did not fit or validate a probabilistic joint model of progression and serviceability with sufficient independence/calibration guarantees.

The multiplication is an operational composition rule, not a probability identity.

Therefore the correct name is **Opportunity Score**.

## When should Growth use Lead Quality instead?

When the objective is:

> maximize scheduled visits regardless of inventory.

## When should Growth use Opportunity Score?

When the objective is:

> prioritize leads likely to progress and serviceable with current/fallback inventory.

## What happens when Inventory cannot serve a lead?

A true non-actionable state receives an actionability gate of zero.

Fallback searches only governed alternatives up to K=3. If no governed result exists, the system allows `NO_RESULT` rather than relaxing indefinitely.

## What is the role of the LLM?

Sampled semantic discovery for Inventory/Catalog QA.

The LLM is not:
- Lead Quality;
- fallback ranking;
- Opportunity Score;
- an automatic QA gate;
- a human-label substitute.

## Why are Semantic Rules not in Lead Quality?

Historical E018 did not support promotion into scoring. The final role is Inventory/Catalog QA.

No post-hoc rule subset is searched to rescue Lift.

## What evidence is clean-room and what is upstream?

Final target, Lead Quality, Inventory, Opportunity V2, capacity, fallback and final audit metrics are AssessmentSol1 authority.

E018/E019/E020 are upstream supporting evidence unless a result was independently reproduced under AssessmentSol1.

PR #19 remains open supplemental LLM evidence.

## What can this assessment not conclude?

It cannot claim:
- causal lift;
- commercial conversion probability;
- a pristine June holdout;
- a jointly calibrated progression × availability probability;
- historically precise budget fit;
- human LLM precision/recall.

A new prospective or external hidden cohort is required for strong post-freeze confirmation.
