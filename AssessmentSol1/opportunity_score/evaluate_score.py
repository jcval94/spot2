from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TARGET_DIR = ROOT / "AssessmentSol1" / "target"
if str(TARGET_DIR) not in sys.path:
    sys.path.insert(0, str(TARGET_DIR))

from build_targets import build_t1_audit, read_raw  # noqa: E402
from build_score import build_scored_population, load_score_config  # noqa: E402


CAPACITIES = (0.05, 0.10, 0.20)


def _partition_expr() -> pl.Expr:
    return (
        pl.when(pl.col("score_time") < pl.datetime(2026, 5, 1))
        .then(pl.lit("DEVELOPMENT"))
        .when(pl.col("score_time") < pl.datetime(2026, 6, 1))
        .then(pl.lit("CALIBRATION"))
        .when(pl.col("score_time") < pl.datetime(2026, 7, 1))
        .then(pl.lit("PROCEDURAL_HOLDOUT_DIAGNOSTIC"))
        .otherwise(pl.lit("POST_HOLDOUT_AUDIT"))
        .alias("population")
    )


def _evaluate_ranked(df: pl.DataFrame, score_col: str, system: str, population: str) -> list[dict[str, Any]]:
    if df.is_empty():
        return []
    positives = int(df["target_value"].sum())
    base_rate = positives / df.height
    if df[score_col].n_unique() <= 1:
        return [{
            "population": population, "system": system, "capacity_pct": int(c * 100),
            "n_leads": math.ceil(df.height * c), "positives_captured": None,
            "recall_at_x": None, "precision_at_x": None, "lift_at_x": None,
            "cumulative_gains": None, "status": "UNDEFINED_CONSTANT_SCORE",
        } for c in CAPACITIES]

    ranked = df.sort(
        [score_col, "inventory_confidence", "lead_id"],
        descending=[True, True, False],
    )
    rows = []
    for c in CAPACITIES:
        n = math.ceil(df.height * c)
        top = ranked.head(n)
        captured = int(top["target_value"].sum())
        precision = captured / n
        recall = captured / positives if positives else None
        rows.append({
            "population": population, "system": system, "capacity_pct": int(c * 100),
            "n_leads": n, "positives_captured": captured, "recall_at_x": recall,
            "precision_at_x": precision, "lift_at_x": (precision / base_rate) if base_rate else None,
            "cumulative_gains": recall,
            "status": ("NON_DEPLOYABLE_REFERENCE" if system == "LEAD_SCORE_INTERNAL_NON_DEPLOYABLE_REFERENCE" else "DEFINED"),
        })
    return rows


def _gains_curve(df: pl.DataFrame, score_col: str, system: str, population: str) -> list[dict[str, Any]]:
    if df.is_empty() or df[score_col].n_unique() <= 1:
        return []
    positives = int(df["target_value"].sum())
    ranked = df.sort([score_col, "inventory_confidence", "lead_id"], descending=[True, True, False])
    rows = []
    for pct in range(1, 101):
        n = math.ceil(df.height * pct / 100)
        captured = int(ranked.head(n)["target_value"].sum())
        rows.append({
            "population": population, "system": system, "population_pct": pct,
            "n_leads": n, "positives_captured": captured,
            "cumulative_gains": captured / positives if positives else None,
        })
    return rows


def evaluate(repo_root: Path, include_holdout: bool = False) -> tuple[pl.DataFrame, pl.DataFrame]:
    cfg = load_score_config()
    if not (HERE / "frozen_score_config.json").exists():
        raise AssertionError("Freeze config must exist before evaluation")
    scored = build_scored_population(repo_root)

    leads, inquiries = read_raw(repo_root)
    target = pl.DataFrame(build_t1_audit(leads, inquiries)).select(
        "lead_id", pl.col("score_time").cast(pl.Datetime), "primary_t1_eligible",
        pl.col("primary_t1_label").cast(pl.Int8).alias("target_value"),
    )
    frame = scored.join(target, on=["lead_id", "score_time"], how="left", validate="1:1")
    frame = frame.filter(pl.col("primary_t1_eligible")).with_columns(_partition_expr())

    # External reference is isolated and never enters the clean score.
    internal = pl.DataFrame(leads).select("lead_id", "lead_score_internal")
    frame = frame.join(internal, on="lead_id", how="left", validate="1:1")

    populations = ["DEVELOPMENT"]
    if include_holdout:
        populations.append("PROCEDURAL_HOLDOUT_DIAGNOSTIC")

    metric_rows: list[dict[str, Any]] = []
    gains_rows: list[dict[str, Any]] = []
    for population in populations:
        part = frame.filter(pl.col("population") == population)
        for system, col in (
            ("LEAD_QUALITY_ONLY", "lead_quality_probability"),
            ("INVENTORY_ONLY", "inventory_serviceability"),
            ("OPPORTUNITY_MULTIPLICATIVE", "opportunity_score_0_100"),
            ("LEAD_SCORE_INTERNAL_NON_DEPLOYABLE_REFERENCE", "lead_score_internal"),
        ):
            metric_rows.extend(_evaluate_ranked(part, col, system, population))
            if system in {"INVENTORY_ONLY", "OPPORTUNITY_MULTIPLICATIVE"}:
                gains_rows.extend(_gains_curve(part, col, system, population))

    metrics = pl.DataFrame(metric_rows)
    gains = pl.DataFrame(gains_rows)
    return metrics, gains


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-holdout", action="store_true",
                        help="Open June only after frozen_score_config.json exists; diagnostic only.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    metrics, gains = evaluate(repo_root, include_holdout=args.include_holdout)
    out = HERE / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    metrics.write_csv(out / "capacity_metrics.csv")
    gains.write_csv(out / "gains_curve.csv")
    print(json.dumps({
        "capacity_rows": metrics.height,
        "gains_rows": gains.height,
        "holdout_included": args.include_holdout,
        "holdout_policy": load_score_config()["holdout_policy"]["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
