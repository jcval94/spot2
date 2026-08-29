# Spot2 Experiment Harness

A deliberately small contract layer for future Spot2 experiments.

It exists to preserve traceability, not to create a second modeling framework.

## Responsibilities

The harness owns four things:

1. Validate the experiment specification.
2. Require a point-in-time leakage review for every newly added feature.
3. State whether a child experiment is directly comparable with its parent.
4. Produce an immutable experiment record with data fingerprints and metrics.

It does **not** currently own:

- feature engineering;
- model training;
- hyperparameter search;
- plotting;
- SHAP;
- clustering;
- LLM execution.

Those remain inside the individual experiment until repeated implementations justify a shared abstraction.

## Skills

Repository-level Codex skills live in:

```text
.agents/skills/
├── spot2-domain/
├── spot2-leakage/
└── spot2-experiment/
```

Their responsibilities are intentionally separate:

| Skill | Question |
|---|---|
| `spot2-domain` | What does this data mean? |
| `spot2-leakage` | Could this information be known at scoring time? |
| `spot2-experiment` | What exactly are we testing relative to the parent? |
| `spot2-experiment-sandbox` | Where may experimental work live and how is it linked to evidence? |

The harness answers:

> What happened when the declared experiment was executed?

## Experiment IDs

New governed experiments should use:

```text
E###_<short_name>
```

and declare `parent_experiment`.

All governed experimental work now lives under `experimentos/`. Legacy work was migrated mechanically without inventing retroactive lineage.

## Validate a spec

```bash
python experimentos/_sistema/harness/experiment_harness.py validate \
  --spec path/to/spec.json \
  --repo-root .
```

For a child experiment:

```bash
python experimentos/_sistema/harness/experiment_harness.py validate \
  --spec path/to/child_spec.json \
  --parent-spec path/to/parent_spec.json \
  --repo-root .
```

The command checks the contract, leakage evidence, data files and direct comparability.

## Finalize a run

Experiment code writes its own results JSON:

```json
{
  "experiment_id": "E001_baseline",
  "metrics": {
    "roc_auc": 0.5,
    "average_precision": 0.4,
    "brier": 0.2,
    "log_loss": 0.7,
    "lift_top_10pct": 1.1,
    "recall_top_20pct": 0.25
  },
  "segment_metrics": {},
  "conclusion": "INCONCLUSIVE",
  "caveats": ["Example only."],
  "next_experiment": "Test one additional feature family."
}
```

Then finalize:

```bash
python experimentos/_sistema/harness/experiment_harness.py finalize \
  --spec path/to/spec.json \
  --results path/to/results.json \
  --output-dir experimentos/Evidencias/harness_records \
  --repo-root .
```

For a child experiment, pass both `--parent-spec` and `--parent-results`.

The harness refuses to overwrite an existing finalized record.

## Comparison status

A child is `EQUIVALENT` to its parent only when these are unchanged:

- scoring time;
- target;
- population;
- data source declarations;
- validation design.

Otherwise it is `NON_EQUIVALENT`.

That is not a failure. It prevents attributing a metric difference to a single feature/model change when the underlying question also changed.

## Data fingerprints

Every finalized record includes SHA-256 fingerprints for declared repository data sources.

This makes a run traceable even if a file at the same path changes later.

## Suggested future structure

Keep all new experimental work inside `experimentos/`; migrate legacy work only when needed to preserve the single sandbox boundary.

For new experiments:

```text
experimentos/
└── E###_<name>/
    ├── spec.json
    ├── run_experiment.py
    └── results.json
```

The finalized harness record can remain a CI artifact or be committed deliberately when the experiment becomes part of the evidence chain.

## Design rule

Only add new harness abstractions after at least two real experiments need the same behavior.
