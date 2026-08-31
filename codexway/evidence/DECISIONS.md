# Frozen methodological decisions

1. Primary contract is T1: one score per lead at its first inquiry, after payload
   persistence and before broker response.
2. Primary target is `scheduled_visit` on that first inquiry, with a seven-day
   maturity buffer and 2026-07-01 data-as-of boundary.
3. T0 is a 30-day sensitivity and must show exposure drift; T2 excludes all
   response history because response event time is not reliable.
4. Availability is attached only with `direction="backward"`. Missing or stale
   history is unknown, never silently converted to unavailable.
5. Market context and mutable spot fields are outside the historical model.
6. Executable model promotion uses rolling train folds and validation; calibration
   uses validation. The procedural holdout is excluded from the gate but is already
   globally consumed, so only new forward data can confirm the result.
7. The stable-segment Logistic may become a forward-shadow candidate only if
   rolling mean and median Lift@10 exceed 1, at least 2/4 folds exceed random,
   validation Lift@10 exceeds 1 and validation Brier remains within tolerance.
   Two weak folds remain a material risk; E117 is not a deployment authorization.
8. Inventory serviceability and Lead Quality remain separate observable axes.
   E114 clears the absolute Lift@10 gate, so it may enter forward validation, but
   its incremental value over Lead Quality remains NO-GO until an aligned fallback
   outcome exists.
9. Cluster cells are hypotheses, not score multipliers. The inherited
   `DN4 × LOC1 × BSV1` label is explicitly non-confirmatory.
10. The LLM is a semantic QA system. Without frozen human gold its incremental
    value on natural listings is incomplete. Controlled injected contradictions
    may measure sensitivity, but are never presented as natural precision.
11. Availability joins are strictly PIT. Historical listing compatibility remains
    conditional until price/geography/attributes have effective-time versions.
12. A retrospective GO authorizes neither automation nor causal claims. The next
    step is forward shadow validation and then a sticky lead-level randomized pilot.
13. Capacity metrics use fractional expected capture at tied score boundaries;
    source-row order is never an operational tie-breaker (E116).
