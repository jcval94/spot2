# Response-time Random Forest experiment

Purpose: test `broker_response_hours` jointly with the rest of the available lead, inquiry and spot context, instead of treating response time as an isolated variable.

## Questions

1. Does response time add out-of-sample predictive information once the rest of the context is included?
2. Is it relevant only in particular subgroups or tree branches?
3. Does the answer change if we predict the immediate `scheduled_visit` response versus a later scheduled visit within 30 days?
4. Is apparent Random Forest impurity importance confirmed by permutation importance?

## Leakage boundary

`broker_response_hours` does not exist at lead arrival or at the instant the inquiry is created. Therefore it is **never proposed as a T0/T1 pre-response feature**.

It is analyzed as an operational diagnostic and as a possible T2 feature after the response occurs.

The experiment excludes known leakage-prone fields such as:

- `lead_score_internal`
- `broker_response` as a predictor
- `total_views`
- `total_inquiries`
- `days_on_market`
- `is_active`

## Outputs

All generated output stays in:

`experiments/response_time_random_forest/results/`

including:

- summary metrics
- raw permutation feature importance
- response-time subgroup analysis
- Random Forest tree branches that split on response time
- response-time sensitivity curves
- plots
- JSON and Markdown report

Run:

```bash
python experiments/response_time_random_forest/run_experiment.py
```
