# Claims policy

## Claims we are allowed to make

- The primary T1 Lead Quality target is a **proxy**: whether the deterministic first inquiry is eventually recorded as `scheduled_visit`.
- The frozen T1 Lead Quality champion is a neutral DEVELOPMENT prevalence prior, not an individual ranking engine.
- Inventory Serviceability is a deterministic, interpretable, point-in-time construct **under the stated structural and business-date assumptions**.
- Candidate Spots are restricted to Spots created by score time.
- Availability in the clean pipeline uses the latest backward snapshot whose business date is not after score time.
- Missing Availability is kept as UNKNOWN rather than coerced to unavailable.
- The Opportunity Score is the frozen product of Lead Quality probability and Inventory Serviceability.
- Because Lead Quality is constant, Opportunity and Inventory have identical ranking in this assessment.
- Offline DEVELOPMENT capacity metrics describe concentration of the **observed scheduled_visit proxy**, not commercial conversion.
- The June period is a **procedural holdout diagnostic**, already non-pristine because of the documented prior incident.
- DEVELOPMENT and June do not demonstrate positive-outcome enrichment for the final ranking.
- The stress tests show that future/unknown-provenance information can change offline metrics while remaining invalid.
- `lead_score_internal` may be reported only as a non-deployable reference.

## Claims we are NOT allowed to make

- That any feature or score **causes** scheduled visits, conversion, revenue or Growth impact.
- That the target is final commercial conversion.
- That an offline lift value proves online incremental impact.
- That top 10% is universally optimal; it is only the declared capacity scenario.
- That June is pristine, truly unseen, an independent final test or independent confirmation.
- That current historical results are confirmatory after the wider research process already inspected the candidate history.
- That a backward Availability snapshot equals the true inventory state at the exact intraday scoring instant; `snapshot_date` has no ingestion timestamp.
- That an old snapshot has the same confidence as a recent one.
- That `UNKNOWN` means unavailable.
- That unversioned current Spot prices were historically known.
- That Spot structural/attribute immutability is proven by raw timestamps; it is an explicit modeling assumption.
- That the T2 stage cohort is fully observable when prior scheduled-visit timing is absent.
- That the final Opportunity Score adds ranking power beyond Inventory in the current frozen model.
- That stress-test improvements justify any production feature or policy change.

## Vocabulary

Use **predictive association** rather than causal effect unless a causal design exists.

Use **scheduled_visit proxy** rather than conversion.

Use **procedural holdout diagnostic** rather than unseen/independent test.

Use **offline capacity metric** rather than business impact.

Use **observed backward snapshot under a business-date assumption** rather than true real-time inventory state.
