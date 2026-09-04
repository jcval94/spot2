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
OUT = ROOT / "outputs" / "metrics" / "user_requested_priority_matrix_collapsed.json"
TARGET = "target_t1"


def segment_lift(g: pd.DataFrame, mask: pd.Series) -> dict:
    seg = g.loc[mask]
    base = float(g[TARGET].mean())
    n = int(len(seg))
    rate = float(seg[TARGET].mean()) if n else float("nan")
    return {"n": n, "rate": rate, "lift": rate / base if n and base > 0 else float("nan")}


def evaluate_monthly(frame: pd.DataFrame) -> dict:
    frame = frame.copy()
    frame["month"] = pd.to_datetime(frame["prediction_timestamp"], utc=True).dt.strftime("%Y-%m")
    topk, exclusive, cumulative = [], [], []
    for month, g in frame.groupby("month", sort=True):
        m = binary_metrics(g[TARGET].astype(int), g["matrix_score"])
        topk.append({
            "month": month, "n": int(len(g)), "positive_rate": float(g[TARGET].mean()),
            "lift_top_5pct": float(m["lift_top_5pct"]),
            "lift_top_10pct": float(m["lift_top_10pct"]),
            "lift_top_20pct": float(m["lift_top_20pct"]),
        })
        for p in [1,2,3,4]:
            vals = segment_lift(g, g["matrix_priority"].eq(p))
            exclusive.append({"month":month,"priority":p,**vals})
        for maxp in [1,2,3]:
            vals = segment_lift(g, g["matrix_priority"].le(maxp))
            cumulative.append({"month":month,"through_priority":maxp,**vals})
    return {"topk":topk,"exclusive":exclusive,"cumulative":cumulative}


def run() -> None:
    settings = load_settings()
    t1 = pd.read_parquet(ABT)
    tables = load_all(settings)
    enriched, _, _ = build_profiles(t1, tables["spots"], tables["inquiries"], seed=settings.seed)
    mature = enriched[enriched[TARGET].notna()].copy()

    train = mature[mature["split"].eq("train")].copy()
    rent = pd.to_numeric(train["requested_budget_mxn_rent_monthly"], errors="coerce")
    median = float(rent.median())
    filled = rent.fillna(median)
    mean = float(filled.mean())
    std = float(filled.std(ddof=0)) or 1.0
    z = (pd.to_numeric(mature["requested_budget_mxn_rent_monthly"], errors="coerce").fillna(median) - mean) / std

    r1 = mature["search_sector"].eq("Industrial") & mature["industry"].eq("retail")
    winner = mature["industrial_small_or_paid_interaction"].eq(1)
    ph1 = mature["physical_profile"].eq("PH1")
    r2 = (~r1) & winner
    r3 = (~r1) & (~winner) & mature["search_sector"].eq("Industrial") & z.ge(-0.239) & z.lt(0.181)
    mature["matrix_priority"] = np.select([r1,r2,r3],[1,2,3],default=4).astype(int)
    mature["matrix_score"] = mature["matrix_priority"].map({1:1.0,2:2/3,3:1/3,4:0.0}).astype(float)
    mature["ph1_annotation"] = winner & ph1

    result = {
        "methodology": {
            "order_selected_from_validation_not_test": True,
            "ph1_not_used_to_break_winner_ties": True,
            "reason": "PH1 is retained as an explanatory subtag because splitting the winner tier reduced monthly top-k stability.",
            "standardization": {"feature":"requested_budget_mxn_rent_monthly","fit":"train only","median":median,"mean":mean,"std_ddof0":std},
        },
        "matrix": [
            {"priority":1,"rule":"search_sector=Industrial AND industry=retail","interpretation":"highest priority"},
            {"priority":2,"rule":"industrial_small_or_paid_interaction=1, excluding priority 1","interpretation":"stable winner; PH1 is annotation only"},
            {"priority":3,"rule":"search_sector=Industrial AND -0.239<=z(rent_budget)<0.181, excluding priorities 1-2","interpretation":"broad stable extension"},
            {"priority":4,"rule":"rest","interpretation":"no rule-based uplift signal"},
        ],
        "test_counts": {},
        "validation": evaluate_monthly(mature[mature["split"].eq("validation")]),
        "test": evaluate_monthly(mature[mature["split"].eq("test")]),
    }
    test = mature[mature["split"].eq("test")]
    result["test_counts"] = {str(k):int(v) for k,v in test["matrix_priority"].value_counts().sort_index().items()}
    result["test_ph1_winner_annotation_n"] = int(test["ph1_annotation"].sum())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
