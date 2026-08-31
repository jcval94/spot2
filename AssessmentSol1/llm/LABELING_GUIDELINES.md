# Human labeling guidelines

## Purpose

Human labels are required before any semantic candidate can be described as a true catalog-quality issue or before human precision/recall can be reported.

The current historical package does **not** contain a complete human-gold labeling set.

Therefore:

`human precision/recall unavailable`.

## Unit of review

One listing (`spot_id`) with:
- title;
- description;
- sector/type/modality;
- relevant structured attributes;
- deterministic Rules-first findings;
- optional LLM residual finding.

## Human label

Choose one:

- `confirmed_issue`: clear semantic/structured inconsistency that warrants catalog correction or investigation.
- `valid_listing`: text and supplied structured data are reasonably compatible.
- `ambiguous`: evidence is insufficient or more than one reasonable interpretation remains.
- `not_verifiable`: the claim cannot be checked from the supplied fields.

## Actionability

A finding is actionable only when a reviewer would create a concrete catalog QA task.

Do not label:
- unusual-but-plausible adaptive use as an issue;
- missing evidence as a contradiction;
- a model's own output as ground truth;
- the S001 discovery-pattern flag as human gold.

## New deterministic rule promotion

A new rule may be proposed only when:

1. humans confirm multiple examples;
2. the pattern is repeatable and expressible deterministically;
3. false-positive controls are reviewed;
4. the rule has a stable semantic definition;
5. it does not depend on future/outcome information.

The validated recurring pattern should then move into Rules vN, leaving the LLM to inspect only the residual long tail.

## Metrics

Without real human gold, report only:
- schema/technical validity;
- Rules overlap;
- residual-class distribution;
- challenge-set behavior versus a **pattern label** when applicable;
- candidate novelty;
- cost/usage.

Do not report human precision, recall, F1, sensitivity, specificity or accuracy unless the comparison target is explicitly a human-gold label. If a challenge metric uses a deterministic discovery pattern, name that comparator explicitly.
