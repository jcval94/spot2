# E016 implementation validation

## Local validation performed before repository update

- `python -m py_compile feature_engineering.py build_abts.py`: PASS.
- `pytest -q tests`: **9 core unit tests passed** in the local isolated suite.

The tests cover:

1. blocked raw features never entering stage feature contracts;
2. structural budget missingness not being median-imputed;
3. `no_response + broker_response_hours` not becoming a realized response;
4. availability using strictly backward as-of snapshots;
5. Land built-environment attributes being gated;
6. amenities using a fixed parsed vocabulary rather than raw list combinations;
7. spot/broker history being reconstructed point-in-time instead of using current totals/raw broker ID;
8. `scheduled_visit` without response timing producing an ambiguous target rather than a false negative.\n9. an unspecified preferred corridor remaining unknown rather than being converted to a false mismatch.

## Important boundary

This validation proves code syntax and critical invariants on synthetic unit cases.

The workflow `.github/workflows/abt-feature-engineering.yml` is included to execute the builder against the repository CSVs. Until that workflow result is consumed, E016 remains:

**IMPLEMENTED / NOT YET BENCHMARKED**

No model lift claim is made.


## Repository-schema contract

A repository-aware test was also added: `test_manifest_covers_repository_source_columns`.

When executed from the full repository it asserts that:

- the treatment manifest has exactly **86** source-variable rows;
- there are no duplicate `table,column` entries;
- the manifest set exactly equals the headers of the six candidate CSVs.

The manifest was constructed from the current source schemas. The GitHub workflow will enforce this invariant on repository execution.

## Full-data execution status

A CI workflow is included to run the builder against the real repository CSVs. In this tool session GitHub did not expose a completed workflow run for the new branch workflow, and the local execution environment cannot resolve github.com to clone the repository.

Therefore no full-data runtime result is fabricated here. The implementation remains **validated at unit/invariant level, with full repository execution automated but not observed in this session**.


## Source-schema verification on merged main

After merge, the manifest was compared directly against the six current source headers on `main`:

| Table | Source columns |
|---|---:|
| leads | 20 |
| spots | 25 |
| spot_attributes | 12 |
| inquiries | 13 |
| availability_snapshot | 6 |
| market_context | 10 |
| **Total** | **86** |

Result:

- manifest rows: **86**;
- source columns: **86**;
- missing manifest entries: **0**;
- extra manifest entries: **0**;
- exact `table,column` set match: **PASS**.

This verifies source-variable coverage. It is distinct from a full runtime build of all Parquet ABTs.
