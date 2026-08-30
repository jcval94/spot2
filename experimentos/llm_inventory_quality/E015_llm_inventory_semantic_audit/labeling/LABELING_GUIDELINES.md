# Human labeling guide — E015 v2

## Objective

Create a human gold set to evaluate whether the LLM adds **actionable** semantic data-quality detection beyond deterministic rules.

The original 200-row `labeling_sample.csv` is now a **discovery sample** because it was inspected during semantic rule discovery. Do not use it as the clean final holdout for the newly promoted S001 rule.

The final comparison uses:

`labeling_holdout_v2.csv`

which excludes every spot in the original discovery sample.

## Primary label

Fill `human_actionable_issue`:

- `1`: at least one clear contradiction or high-confidence semantic cross-field mismatch merits catalog review.
- `0`: no issue that merits catalog review.
- leave blank temporarily when genuinely ambiguous; explain in `human_notes`.

Do **not** set the primary label to 1 merely because a claim is unsupported by the supplied schema or cannot be verified from the available columns.

## Actionable classes

### contradiction

Requires all three:
1. explicit textual claim;
2. directly comparable structured field;
3. incompatible values.

Example:
- “buena iluminación natural”
- `natural_light=false`

### semantic_cross_field_mismatch

Requires a clear coherence problem across fields even when there is no one-to-one comparable attribute.

Example class:
- `sector_name=Land`
- building/interior-condition language such as “recién remodelado”, “acabados modernos” or “listo para ocupar”.

This is a QA signal, not proof that either source is factually correct.

## Non-actionable by default

These do not make `human_actionable_issue=1` on their own:

- `unsupported_claim`
- `not_verifiable`
- `ambiguous`
- `consistent`

Examples:
- “zona de alta plusvalía” without a comparable supplied field;
- “fácil acceso a transporte público” without accessibility data;
- “Retail ideal para oficinas corporativas” when re-use remains plausible;
- security wording where the ontology does not define whether `basic` or `cctv` conflicts with the claim.

## Claim-level labels

Use `human_claim_labels_json` for auditable detail:

```json
[
  {
    "claim_type": "cross_field_semantics",
    "classification": "semantic_cross_field_mismatch",
    "actionable": true,
    "evidence_text": "Recién remodelado con acabados modernos.",
    "structured_field": "sector_name",
    "structured_value": "Land"
  }
]
```

Allowed classifications:

- `consistent`
- `contradiction`
- `semantic_cross_field_mismatch`
- `unsupported_claim`
- `ambiguous`
- `not_verifiable`

## Blind-review rule

For the strongest evaluation, review title, description and structured attributes **without seeing**:

- LLM output;
- `rules_v1_positive`;
- `rules_v2_positive`;
- rule issue-type columns.

Freeze human labels before comparing systems.

## Discovery leakage note

The S001 Land × building-copy rule was discovered after inspecting the original 200-row discovery sample. Therefore:

- `Rules v1` remains frozen as the original baseline;
- `Rules v2` is explicitly labeled post-discovery;
- `labeling_holdout_v2.csv` excludes the discovery sample and is required for fair evaluation of S001.
