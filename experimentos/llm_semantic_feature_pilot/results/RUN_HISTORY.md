# E017 run history

## Authoritative result

### Workflow run 33296462871 — SUCCESS

This is the authoritative V2 result used by E017.

- status: success;
- model: `gpt-5-nano`;
- records: 100;
- batches: 5 × 20;
- artifact: `9727563377`;
- input tokens: 12,634;
- output tokens: 4,869;
- estimated cost: USD 0.002579.

Outputs produced:

- `pilot_llm_results_100_v2.csv`;
- `pilot_usage_summary_v2.csv`;
- `pilot_segment_summary_v2.csv`;
- `pilot_diagnostic_gates_v2.csv`.

## Earlier V1

V1 also completed over 100 records and cost approximately USD 0.003335.

It was not promoted because redundant LLM-generated fields allowed logical contradictions such as:

- `incremental_issue=false`;
- while `new_rule_candidate=true` or `requires_human_review=true`.

V2 corrected the contract by asking the model for fewer independent decisions and deriving redundant flags deterministically in Python.

This reduced output tokens from 6,767 to 4,869, approximately **28%**.

## Later rerun 33296587433 — FAILURE

A later workflow rerun failed in `run_pilot_v2.py` with:

`RuntimeError: Batch 2 ID mismatch`

Before the failure:

- dependency installation passed;
- 5 contract tests passed;
- the free semantic rule sidecar was built successfully.

This failed rerun **does not replace or invalidate** the earlier successful authoritative V2 run. It indicates a robustness issue in batch-response ID handling that should be fixed before future API reruns.

No metrics from the failed rerun are used in the E017 conclusion.

## Rule sidecar build observed in failed rerun

The deterministic build completed before the API failure and reported:

- `rule_direct_conflict_flag`: 322;
- `rule_land_building_copy_flag`: 230;
- `rule_semantic_ambiguity_flag`: 429.

These counts are consistent with the documented full-catalog sidecar results.
