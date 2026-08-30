# E016 implementation validation

## Local validation performed before repository update

- `python -m py_compile feature_engineering.py build_abts.py`: PASS.
- `pytest -q tests`: **8 passed**.

The tests cover:

1. blocked raw features never entering stage feature contracts;
2. structural budget missingness not being median-imputed;
3. `no_response + broker_response_hours` not becoming a realized response;
4. availability using strictly backward as-of snapshots;
5. Land built-environment attributes being gated;
6. amenities using a fixed parsed vocabulary rather than raw list combinations;
7. spot/broker history being reconstructed point-in-time instead of using current totals/raw broker ID;
8. `scheduled_visit` without response timing producing an ambiguous target rather than a false negative.

## Important boundary

This validation proves code syntax and critical invariants on synthetic unit cases.

The workflow `.github/workflows/abt-feature-engineering.yml` is included to execute the builder against the repository CSVs. Until that workflow result is consumed, E016 remains:

**IMPLEMENTED / NOT YET BENCHMARKED**

No model lift claim is made.
