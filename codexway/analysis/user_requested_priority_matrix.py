from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from spot2_codexway.contracts import load_settings
from spot2_codexway.data import load_all
from spot2_codexway.evaluation import binary_metrics
from spot2_codexway.profiles import build_profiles

ROOT = Path(__file__).resolve().parents[1]
ABT = ROOT / "outputs" / "abt" / "abt_t1_first_inquiry.parquet"
OUT_JSON = ROOT / "outputs" / "metrics" / "user_requested_priority_matrix.json"
OUT_CSV = ROOT / "outputs" / "metrics" / "user_requested_priority_matrix_monthly.csv"
TARGET = "target_t1"


def segment_monthly(frame: pd.DataFrame, mask_col: str, label: str) -> list[dict]:
    out = []
    for month, g in frame.groupby("month", sort=True):
        seg = g[g[mask_col]]
        base = float(g[TARGET].mean())
        n = int(len(seg))
        rate = float(seg[TARGET].mean()) if n else float("nan")
        out.append({
            "kind": "exclusive_tier",
            "label": label,
            "month": month,
            "n": n,
            "positive_rate": rate,
            "month_baseline": base,
            "lift": rate / base if n and base > 0 else float("nan"),
        })
    return out


def cumulative_monthly(frame: pd.DataFrame, max_priority: int, label: str) -> list[dict]:
    out = []
    for month, g in frame.groupby("month", sort=True):
        seg = g[g["priority_num"].le(max_priority)]
        base = float(g[TARGET].mean())
        n = int(len(seg))
        rate = float(seg[TARGET].mean()) if n else float("nan")
        out.append({
            "kind": "cumulative",
            "label": label,
            "month": month,
            "n": n,
            "positive_rate": rate,
            "month_baseline": base,
            "lift": rate / base if n and base > 0 else float("nan"),
        })
    return out


def policy_topk_monthly(frame: pd.DataFrame) -> list[dict]:
    rows = []
    for month, g in frame.groupby("month", sort=True):
        metrics = binary_metrics(g[TARGET].astype(int), g["priority_score"])
        rows.append({
            "month": month,
            "n": int(len(g)),
            "positive_rate": float(g[TARGET].mean()),
            "lift_top_5pct": float(metrics["lift_top_5pct"]),
            "lift_top_10pct": float(metrics["lift_top_10pct"]),
            "lift_top_20pct": float(metrics["lift_top_20pct"]),
        })
    return rows


def run() -> None:
    settings = load_settings()
    t1 = pd.read_parquet(ABT)
    tables = load_all(settings)
    enriched, _, _ = build_profiles(t1, tables["spots"], tables["inquiries"], seed=settings.seed)
    mature = enriched[enriched[TARGET].notna()].copy()

    # Train-only standardization for the one numeric rule used in the matrix.
    train = mature[mature["split"].eq("train")].copy()
    rent = pd.to_numeric(train["requested_budget_mxn_rent_monthly"], errors="coerce")
    rent_median = float(rent.median())
    rent_filled = rent.fillna(rent_median)
    rent_mean = float(rent_filled.mean())
    rent_std = float(rent_filled.std(ddof=0))
    if not np.isfinite(rent_std) or rent_std == 0:
        rent_std = 1.0
    all_rent = pd.to_numeric(mature["requested_budget_mxn_rent_monthly"], errors="coerce").fillna(rent_median)
    mature["z_requested_budget_mxn_rent_monthly"] = (all_rent - rent_mean) / rent_std

    mature["rule_industrial_retail"] = mature["search_sector"].eq("Industrial") & mature["industry"].eq("retail")
    mature["rule_winner"] = mature["industrial_small_or_paid_interaction"].eq(1)
    mature["rule_winner_ph1"] = mature["rule_winner"] & mature["physical_profile"].eq("PH1")
    mature["rule_industrial_rent_band"] = (
        mature["search_sector"].eq("Industrial")
        & mature["z_requested_budget_mxn_rent_monthly"].ge(-0.239)
        & mature["z_requested_budget_mxn_rent_monthly"].lt(0.181)
    )

    # Hierarchy fixed from validation evidence: no test-driven ordering.
    conditions = [
        mature["rule_industrial_retail"],
        (~mature["rule_industrial_retail"]) & mature["rule_winner_ph1"],
        (~mature["rule_industrial_retail"]) & (~mature["rule_winner_ph1"]) & mature["rule_winner"],
        (~mature["rule_industrial_retail"]) & (~mature["rule_winner_ph1"]) & (~mature["rule_winner"]) & mature["rule_industrial_rent_band"],
    ]
    mature["priority_num"] = np.select(conditions, [1, 2, 3, 4], default=5).astype(int)
    # Valid ordinal score in [0,1], preserving P1>P2>P3>P4>P5 without probability clipping.
    mature["priority_score"] = (5 - mature["priority_num"]).astype(float) / 4.0
    mature["priority_label"] = mature["priority_num"].map({
        1: "P1 Industrial + industry=retail",
        2: "P2 Winner + PH1 (exclusive)",
        3: "P3 Winner remainder (exclusive)",
        4: "P4 Industrial + central rent-z band (exclusive)",
        5: "P5 Rest",
    })

    matrix = [
        {"priority": 1, "rule": "search_sector=Industrial AND industry=retail", "validation_min_lift": 1.532609, "validation_mean_lift": 1.828834},
        {"priority": 2, "rule": "winner=1 AND physical_profile=PH1, excluding P1", "validation_min_lift": 1.468750, "validation_mean_lift": 1.499454},
        {"priority": 3, "rule": "winner=1, excluding P1/P2", "validation_min_lift": 1.325188, "validation_mean_lift": 1.447399},
        {"priority": 4, "rule": "search_sector=Industrial AND -0.239<=z(rent_budget)<0.181, excluding P1/P2/P3", "validation_min_lift": 1.063830, "validation_mean_lift": 1.228586},
        {"priority": 5, "rule": "rest", "validation_min_lift": None, "validation_mean_lift": None},
    ]

    result = {
        "methodology": {
            "target": TARGET,
            "matrix_order_selected_from_validation_not_test": True,
            "rules_are_exclusive_by_precedence": True,
            "numeric_standardization": {
                "feature": "requested_budget_mxn_rent_monthly",
                "imputation": "train median",
                "mean": rent_mean,
                "std_ddof0": rent_std,
                "fit_split": "train",
            },
            "policy_topk_tie_handling": "spot2_codexway.evaluation.binary_metrics tie-aware expected top-k",
        },
        "matrix": matrix,
        "splits": {},
    }

    monthly_rows: list[dict] = []
    for split in ["validation", "test"]:
        frame = mature[mature["split"].eq(split)].copy()
        frame["month"] = pd.to_datetime(frame["prediction_timestamp"], utc=True).dt.strftime("%Y-%m")
        split_out = {
            "n": int(len(frame)),
            "prevalence": float(frame[TARGET].mean()),
            "priority_counts": {str(k): int(v) for k, v in frame["priority_num"].value_counts().sort_index().items()},
            "exclusive_tiers_monthly": [],
            "cumulative_monthly": [],
            "policy_topk_monthly": policy_topk_monthly(frame),
        }
        for priority in [1, 2, 3, 4, 5]:
            col = f"is_p{priority}"
            frame[col] = frame["priority_num"].eq(priority)
            rows = segment_monthly(frame, col, f"P{priority}")
            split_out["exclusive_tiers_monthly"].extend(rows)
            for r in rows:
                monthly_rows.append({"split": split, **r})
        for max_p, label in [(1, "P1"), (2, "P1-P2"), (3, "P1-P3"), (4, "P1-P4")]:
            rows = cumulative_monthly(frame, max_p, label)
            split_out["cumulative_monthly"].extend(rows)
            for r in rows:
                monthly_rows.append({"split": split, **r})
        result["splits"][split] = split_out

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(monthly_rows).to_csv(OUT_CSV, index=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
