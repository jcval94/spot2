# Rules-first baseline

## Role

The deterministic rules are the production baseline for repeatable listing-copy inconsistencies. They run before any LLM and require no external inference.

The LLM is allowed to inspect only the unresolved semantic residual. A recurring human-validated residual pattern should be converted back into a deterministic rule rather than creating a permanent API dependency.

## Canonical rule families

### R001 — natural-light contradiction

Trigger:
- listing explicitly claims natural light;
- structured `natural_light == false`.

### R002 — security contradiction

Trigger:
- listing explicitly claims security/access-control language;
- `security_type` is missing or `none`.

### R003 — parking contradiction

Trigger:
- listing claims parking;
- `parking_spaces` is zero/missing;
- `parking` is absent from amenities.

### R004 — readiness contradiction

Trigger:
- listing claims ready/remodeled/modern condition;
- `building_status == needs_renovation`.

## Semantic sidecar rules

The E017 discovery process also produced deterministic semantic patterns:

- `rule_land_building_copy_flag`;
- `rule_security_ambiguity_flag`;
- `rule_retail_adaptive_use_flag`;
- `rule_semantic_ambiguity_flag`;
- `rule_semantic_signal_count`;
- `rule_semantic_review_tier`.

These are retained for Inventory/Catalog QA only. E018 showed they do not satisfy the gate for Lead Quality scoring.

## Clean-room reproduction

Prompt 12 reproduced the rules directly from raw Spot + attribute data:

| Metric | Count | Share |
|---|---:|---:|
| listings | 3,000 | 100.00% |
| direct conflict flag | 322 | 10.73% |
| Land × building copy | 230 | 7.67% |
| security ambiguity | 327 | 10.90% |
| Retail adaptive-use language | 109 | 3.63% |
| any semantic ambiguity | 429 | 14.30% |
| at least one semantic signal | 890 | 29.67% |
| two simultaneous signals | 91 | 3.03% |

Review tiers:
- none: 2,110;
- ambiguity: 386;
- direct_conflict: 322;
- cross_field: 182.

The executable implementation is in `run_llm_audit.py`; `--mode rules` performs this reproduction without an OpenAI key.
