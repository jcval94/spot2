from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CAPACITIES = (0.05, 0.10, 0.15, 0.20)


def _evaluate_ranked(df: pl.DataFrame, score_col: str, system: str, population: str) -> list[dict[str, Any]]:
    if df.is_empty():
        return []
    positives = int(df["target_value"].sum())
    base_rate = positives / df.height
    ranked = df.sort([score_col, "lead_id"], descending=[True, False])
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
            "cumulative_gains": recall, "status": "DEFINED",
        })
    return rows


def main() -> None:
    # Authoritative post-recovery evaluation is fold-relative and is persisted by Prompt 11.6.
    src = ROOT / "AssessmentSol1" / "recovery_downstream" / "CAPACITY_REEVALUATION.csv"
    x = pl.read_csv(src)
    macro = x.filter(pl.col("aggregation") == "MACRO")
    out = HERE / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    macro.write_csv(out / "capacity_metrics.csv")
    print({"rows": macro.height, "authority": str(src)})


if __name__ == "__main__":
    main()
