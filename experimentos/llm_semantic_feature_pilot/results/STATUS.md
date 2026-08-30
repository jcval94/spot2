# Execution status

**PILOT EXECUTED / LLM FEATURES NOT PROMOTED**

## V1

- model: `gpt-5-nano`
- 100 records
- estimated cost: USD 0.003335
- rejected for feature promotion because redundant LLM-generated fields produced logical contradictions.

## V2

- model: `gpt-5-nano`
- 100 records
- input tokens: 12,634
- output tokens: 4,869
- estimated cost: USD 0.002579
- clean-control incremental issue rate: 0%
- new rule candidates: 0
- residual actionable: 0

Decision: **NOT_SUPPORTED** for adding LLM-derived variables to the current ABT.

The semantics found by V2 were already representable through deterministic rule flags. A free semantic rule sidecar is implemented instead.

Full 100-row V2 output was produced by workflow run `33296462871`, artifact `9727563377`.


## Authoritative run

- workflow: `33296462871`
- conclusion: **success**
- artifact: `9727563377`

A later rerun `33296587433` failed with `Batch 2 ID mismatch`. It is not used for metrics or conclusions.

See [RUN_HISTORY.md](RUN_HISTORY.md) for the exact distinction and [DECISION_LLM_FEATURES.md](../DECISION_LLM_FEATURES.md) for the production decision.
