# Human labeling guide — E015

## Objective

Create a small human gold set to evaluate whether Rules-only, LLM-only or Rules+LLM actually detects actionable semantic data-quality issues.

## Primary label

Fill `human_actionable_issue`:

- `1`: at least one clear copy-vs-structured inconsistency or unsupported material claim merits catalog review.
- `0`: no meaningful issue requiring review.
- leave blank temporarily when genuinely ambiguous; explain in `human_notes`.

Do **not** label a row as problematic merely because the copy is generic, repetitive or unattractive.

## Claim-level labels

Use `human_claim_labels_json` for auditable detail, for example:

```json
[
  {
    "claim_type": "natural_light",
    "classification": "contradiction",
    "evidence_text": "Amplio espacio con buena iluminación natural.",
    "structured_field": "natural_light",
    "structured_value": false
  }
]
```

Allowed classifications:

- `consistent`
- `contradiction`
- `unsupported_claim`
- `ambiguous`
- `not_verifiable`

## Decision rules

A contradiction requires:
1. an explicit textual claim;
2. a directly comparable structured field;
3. incompatible values.

If the field is absent, prefer `not_verifiable` or `unsupported_claim`.

A text/field conflict does **not** establish which source is factually correct. The gold label only says that a human catalog review is warranted.

## Leakage / blind review

For the strongest evaluation, the reviewer should assess title, description and structured attributes **without seeing the LLM output**.

The `rule_positive` and `rule_issue_types` columns are included for traceability; ideally hide them during manual review and reveal them only after labels are frozen.
