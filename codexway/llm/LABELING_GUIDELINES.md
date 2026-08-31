# Blind human labeling guide

Label the copy against the structured fields without looking at rule or LLM
outputs. The unit is one `spot_id`.

- `human_actionable_issue = 1`: the supplied text contains explicit evidence of
  a contradiction or a material cross-field mismatch that an inventory operator
  should investigate.
- `human_actionable_issue = 0`: the record is consistent, merely promotional,
  unverifiable from the payload, or genuinely ambiguous.
- Leave the label blank only when a reviewer cannot decide. Explain the reason in
  `human_notes`.

Use `human_issue_type` from: `contradiction`,
`semantic_cross_field_mismatch`, `none`, `uncertain`. Do not infer facts from a
map, website, brand familiarity, or market knowledge. A second reviewer should
adjudicate disagreements. Freeze the CSV before running evaluation.

