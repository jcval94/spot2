# Spot2 Lead Opportunity Score — codexway

## 1. Executive summary

This directory is an isolated, reproducible implementation of the Spot2 Data
Science assessment. It ranks leads while separately measuring whether current
inventory can serve them. The priority is a deployable temporal contract—not the
largest possible AUC.

The primary prediction is **T1: one score per lead at the first inquiry**, after
the request has been persisted and before any broker response is known.

```text
calibrated P(first inquiry schedules a visit)
                 ×
point-in-time inventory serviceability
                 ↓
       Lead Opportunity Score
```

`data/` and `experimentos/` are read-only inputs/evidence. No runtime import comes
from `experimentos/`; provenance is recorded in `evidence/` and `harness/UPSTREAM.md`.

## 2. Problem definition

The system has four outputs:

1. Lead Quality probability and score (0–100).
2. Inventory Serviceability and confidence.
3. Combined Lead Opportunity Score (0–100) and capacity band.
4. Up to five explainable fallback spots when the requested spot is not attendable.

The offline target is a commercial progress proxy, not a closed deal or causal
business outcome.

## 3. Prediction timestamp

### Primary T1

- Grain: one row per `lead_id`, retaining its first `inquiry_id`.
- Timestamp: first `inquiry_at`, tie-broken by `inquiry_id`.
- Operational moment: current inquiry known; broker response unknown.

### Secondary T0

At `lead.created_at`, predict whether any inquiry initiated in the next 30 days
schedules a visit. T0 is a sensitivity because its target drifts with the number of
inquiries a lead gets during the observation window.

### Challenger T2

At later inquiries, use the current payload plus strictly shifted historical
inquiry payloads. Broker response history is excluded because no reliable response
event timestamp exists.

## 4. Target, maturity and censoring

T1 is positive when the **first inquiry** has
`broker_response == "scheduled_visit"`. A seven-day maturity buffer is applied to
a data-as-of boundary of `2026-07-01T00:00:00Z`; therefore a first inquiry is
evaluable only before `2026-06-24`.

- 4,898 mature leads;
- 1,001 positives (20.44%);
- 102 recent leads with `target = NA`, still scoreable.

Sensitivity targets include 14/30-day maturity, `accepted_or_scheduled`, and any
scheduled inquiry initiated in the next 30 days. `broker_response_hours` is never
used for maturity, target timing or features.

## 5. Leakage prevention

The model consumes an explicit allowlist from `config/feature_policy.yaml`. A
column cannot enter merely because it exists in the ABT.

Blocked from the clean model:

- `lead_score_internal` (benchmark/stress only);
- `broker_response` and `broker_response_hours`;
- later inquiries or future aggregates;
- `days_on_market`, `total_views`, `total_inquiries`, `is_active`;
- `competing_inquiries_30d`;
- `market_context` (publication/effective time unknown);
- LLM/text features without historical versions.

Availability uses only:

```python
pd.merge_asof(..., direction="backward")
```

`snapshot_date <= prediction_timestamp` is enforced by code and tests. Missing or
stale snapshots mean unknown/low confidence, not unavailable. See
`evidence/LEAKAGE_MATRIX.md`.

## 6. Data

The six canonical Parquet files are loaded from `data/candidate/parquet`. CSVs are
read only to prove cell-level equivalence and are never concatenated. Audit output
includes schemas, primary/foreign keys, missingness, dates and known semantic
traps.

ABTs:

- `abt_t0_lead_creation.parquet`;
- `abt_t1_first_inquiry.parquet`;
- `abt_t2_rescore.parquet`;
- `abt_inventory_candidates.parquet`;
- `lead_opportunity_scores.parquet/csv`.

## 7. Features and clustering

Clean T1 features cover lead intake, the current inquiry payload and reproducible
T0→T1 consistency ratios. Spot state and availability are held in the inventory
component to keep Lead Quality conceptually separate.

Profiles are refit on train only:

- Search Need (K-Means, K=3);
- Dynamic Need (K-Means, K=5);
- Physical (GMM, K=4);
- Location (K-Means, K=7);
- auxiliary Broker Service (Bisecting K-Means, K=3).

Cells require N≥50, empirical-Bayes shrinkage, Wilson intervals and
Benjamini–Hochberg FDR at 10%. `DN4 × LOC1 × BSV1` is a pre-registered inherited
hypothesis—not a 1.51× multiplier or confirmed discovery.

## 8. Validation and modeling

The primary split is chronological with seven-day purges:

| Partition | First-inquiry interval | N | Positive rate |
|---|---|---:|---:|
| Train | 2025-01-01 to 2025-09-23 | 2,191 | 20.22% |
| Validation | 2025-10-01 to 2025-12-23 | 847 | 19.48% |
| Holdout | 2026-01-01 to 2026-06-23 | 1,711 | 21.22% |

Model progression is deliberately small: global rate, business rule, broad
Logistic Regression, CatBoost and a stability-constrained Logistic challenger.
The promoted challenger uses one T0-safe interaction:
`Industrial AND (company_size=small OR source=paid)`. It replaces unstable
high-cardinality geography with an interpretable capacity-ranking segment.

Forward-candidate promotion requires rolling mean and median Lift@10 >1, at least
two of four temporal folds above random, validation Lift@10 >1 and no material
validation Brier degradation. E117 uses this aggregate gate because the small
rolling folds are noisy; it does not conceal that two folds remain below random.
The rolling mean/median are 1.214x/1.159x and fixed-validation Lift@10 is 1.442x.
Platt scaling is fit on validation and kept only if it improves Brier or
Log Loss. The historical holdout is procedural, not globally virgin, because prior
experiments inspected outcomes from the same data.
The interaction hypothesis was also formulated after that global consumption;
therefore its holdout result is retrospective evidence, not a pristine discovery.
Because the challenger is deliberately low-cardinality, capacity metrics use
fractional expected capture when a score tie crosses the capacity boundary. This
makes Lift invariant to input row order; E116 records that evaluation correction.

## 9. Evaluation

The pipeline reports ROC-AUC, PR-AUC, Log Loss, Brier, calibration,
Precision/Recall@5/10/20%, Lift@5/10% and cumulative gains. It also produces
segment metrics, drift, cluster diagnostics, error analysis and model importance.

The operational question is answered directly by `Recall@X`: what share of
positive outcomes is captured when only the top X% can be worked?

Lead Quality, the inventory lower/upper bounds and both Opportunity bounds are
evaluated on the identical procedural holdout. Bootstrap confidence intervals and
paired deltas are written to `outputs/metrics/system_score_*`. On the procedural
holdout, Lead Quality reaches tie-aware Lift@10 **1.689x** (95% bootstrap CI
1.381–1.982) and conservative Opportunity reaches **1.370x** (1.078–1.690).
Inventory does not improve ranking over Lead Quality alone; its incremental gate
remains NO-GO. Because the T1 target does not observe whether a fallback
recommendation succeeds, this is not a calibrated inventory-outcome claim.

## 10. Inventory and business recommendation

Candidate spots must already exist and satisfy sector/modality gates. Fit combines
area, price, geography and historical availability. Availability has explicit
lower/upper bounds: a missing or stale snapshot is unknown, so it contributes 0
to the conservative bound and 1 to the optimistic availability bound. Fallback
relaxes corridor → municipality → state and returns reason codes.

```text
Lead Quality Score = 100 × calibrated probability
Opportunity Score  = 100 × probability × inventory serviceability
```

Bands are frozen from validation percentiles and retained as capacity summaries;
they are not universal routing thresholds. Capacity scenarios of 5%, 10% and 20%
are reported. Both Lead Quality and conservative Opportunity now clear the
absolute Lift@10 gate with bootstrap lower bounds above 1. The decision is
**eligible for a new forward shadow period and guarded randomized pilot**, not
immediate automation. The UI should still preserve Lead Quality and Inventory
Confidence/Serviceability as separate axes.

Availability itself is point-in-time correct. The full historical matching score
is only **conditional**, because price, area, geography and other listing fields
have no version history. `spot.created_at <= t` proves existence, not that every
stored attribute had the same value at `t`.
An online sticky lead-level A/B protocol is emitted for future use because offline
lift is not causal impact.

The same lift/leakage gates run independently in
`.github/workflows/codexway-lift-gate.yml`; external LLM calls are disabled in CI.

## 11. LLM contribution

The LLM is a **Semantic Inventory Quality Auditor**, not a decorative explanation
layer. It compares listing copy with structured fields under a versioned prompt
and strict JSON Schema. Outputs are cached by input/prompt/schema/model hash, with
model ID, latency, errors and schema-valid rate recorded.

Evaluation compares Rules-only, LLM-only, union and high-precision intersection on
240 general + 100 Land challenge rows. A controlled injected-contradiction set
measures detection recall and is explicitly not a precision estimate. Human
reviewers must still freeze blind natural labels before accuracy or incremental-
recall claims on real listings are valid. The run records token usage, returned
model ID, latency, errors and schema validity. Text features never enter the
historical Lead Quality model because the copy is not versioned over time.

## 12. Leakage stress tests

Three deliberately invalid conditions are evaluated under the same holdout and
marked `NON_DEPLOYABLE`:

- internal score;
- future inquiry information;
- nearest/future availability snapshots.

Their purpose is to quantify artificial performance, not to select a model. Unsafe
specifications cannot produce a deployable harness record.

## 13. Reproduction

Python 3.11–3.13 is supported. From the repository root:

```powershell
python -m pip install -e ".\codexway[dev]"
python codexway/scripts/run_all.py
python -m pytest codexway/tests -q
```

For the exact validated direct + transitive environment:

```powershell
python -m pip install -r codexway/requirements.lock
python -m pip install -e codexway --no-deps
```

Regenerate the lock only from an intentionally updated, tested environment with
`python codexway/scripts/generate_lock.py`.

The live semantic audit requires `OPENAI_API_KEY` (or legacy `OPENAIAPI`). For a
local structural run that deliberately skips external inference:

```powershell
python codexway/scripts/run_all.py --skip-live-llm
```

Useful stages:

```powershell
python -m spot2_codexway.pipeline audit
python -m spot2_codexway.pipeline build-abt
python -m spot2_codexway.pipeline run-llm-audit --limit 10
```

Outputs are written only inside `codexway/outputs`, `codexway/reports` and
`codexway/notebooks`. The end-to-end manifest contains data fingerprints and
status. Re-running with the same inputs/seed must preserve splits and predictions
within numerical tolerance; live API latency/cost metadata is naturally variable.

## 14. Deliverables and limitations

Generated deliverables:

- executed notebook and HTML;
- one-page PDF;
- seven-slide PDF;
- model card, A/B protocol and evidence ledger;
- ABTs, predictions, metrics, figures and experiment records.

Important limitations: synthetic/small data, proxy outcome, globally consumed
historical holdout, a combined target not aligned to fallback success, missing
historical versions for listing text and listing state, availability coverage
drift, and absent human semantic gold until labeling is completed.
