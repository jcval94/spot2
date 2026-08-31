from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ABT = ROOT / "abt"
LQ = ROOT / "models" / "lead_quality"
FEATURES = ROOT / "features"
for p in (ABT, LQ, FEATURES):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from build_t0 import build_t0
from train import fit_logistic
from evaluate import metric_bundle

RANDOM_SEED = 20260830

RAW = [
    "user_type","company_size","industry","search_sector","search_modality",
    "target_area_sqm","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly",
    "min_budget_mxn_sale_total","max_budget_mxn_sale_total","preferred_state",
    "preferred_municipality","preferred_corridor","source",
]
DERIVED = [
    "rent_budget_applicable","sale_budget_applicable","intake_rent_budget_state",
    "intake_sale_budget_state","intake_rent_budget_midpoint","intake_sale_budget_midpoint",
    "intake_rent_budget_width","intake_sale_budget_width","intake_budget_bounds_consistent",
    "intake_geography_specificity","intake_constraint_count","intake_completeness_rate",
    "log1p_target_area_sqm",
]
FEATURE_SET = RAW + DERIVED


def _state(app: pd.Series, lo: pd.Series, hi: pd.Series) -> pd.Series:
    return pd.Series(
        np.select(
            [
                ~app,
                lo.notna() & hi.notna(),
                lo.notna() ^ hi.notna(),
            ],
            ["NOT_APPLICABLE", "OBSERVED", "PARTIAL"],
            default="UNKNOWN",
        ),
        index=app.index,
    )


def add_intake_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    rent = out["search_modality"].isin(["rent", "both"])
    sale = out["search_modality"].isin(["sale", "both"])
    out["rent_budget_applicable"] = rent
    out["sale_budget_applicable"] = sale
    out["intake_rent_budget_state"] = _state(
        rent, out["min_budget_mxn_rent_monthly"], out["max_budget_mxn_rent_monthly"]
    )
    out["intake_sale_budget_state"] = _state(
        sale, out["min_budget_mxn_sale_total"], out["max_budget_mxn_sale_total"]
    )
    out["intake_rent_budget_midpoint"] = (
        out["min_budget_mxn_rent_monthly"] + out["max_budget_mxn_rent_monthly"]
    ) / 2
    out["intake_sale_budget_midpoint"] = (
        out["min_budget_mxn_sale_total"] + out["max_budget_mxn_sale_total"]
    ) / 2
    out["intake_rent_budget_width"] = (
        out["max_budget_mxn_rent_monthly"] - out["min_budget_mxn_rent_monthly"]
    )
    out["intake_sale_budget_width"] = (
        out["max_budget_mxn_sale_total"] - out["min_budget_mxn_sale_total"]
    )
    out["intake_budget_bounds_consistent"] = (
        (~rent)
        | out["min_budget_mxn_rent_monthly"].isna()
        | out["max_budget_mxn_rent_monthly"].isna()
        | (out["min_budget_mxn_rent_monthly"] <= out["max_budget_mxn_rent_monthly"])
    ) & (
        (~sale)
        | out["min_budget_mxn_sale_total"].isna()
        | out["max_budget_mxn_sale_total"].isna()
        | (out["min_budget_mxn_sale_total"] <= out["max_budget_mxn_sale_total"])
    )
    out["intake_geography_specificity"] = out[
        ["preferred_state", "preferred_municipality", "preferred_corridor"]
    ].notna().sum(axis=1)
    out["intake_constraint_count"] = (
        out[["target_area_sqm","preferred_state","preferred_municipality","preferred_corridor"]]
        .notna().sum(axis=1)
        + (rent & out[["min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly"]].notna().any(axis=1)).astype(int)
        + (sale & out[["min_budget_mxn_sale_total","max_budget_mxn_sale_total"]].notna().any(axis=1)).astype(int)
    )
    core = ["user_type","search_sector","search_modality","target_area_sqm","source",
            "company_size","industry","preferred_state","preferred_municipality","preferred_corridor"]
    numerator = out[core].notna().sum(axis=1).astype(float)
    denominator = pd.Series(float(len(core)), index=out.index)
    numerator += (rent & out[["min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly"]].notna().any(axis=1)).astype(float)
    numerator += (sale & out[["min_budget_mxn_sale_total","max_budget_mxn_sale_total"]].notna().any(axis=1)).astype(float)
    denominator += rent.astype(float) + sale.astype(float)
    out["intake_completeness_rate"] = numerator / denominator
    out["log1p_target_area_sqm"] = np.log1p(out["target_area_sqm"].clip(lower=0))
    return out


def main() -> None:
    repo_root = HERE.parents[3]
    _, model = build_t0(repo_root)
    df = add_intake_features(model.to_pandas())
    df["score_time"] = pd.to_datetime(df["score_time"], utc=True)
    contract = json.loads((ROOT / "splits" / "split_contract.json").read_text())

    rows = []
    for fold in contract["folds"]:
        start = pd.Timestamp(fold["validation_start"])
        end = pd.Timestamp(fold["validation_end_exclusive"])
        train = df.loc[df["score_time"] < start].copy()
        val = df.loc[(df["score_time"] >= start) & (df["score_time"] < end)].copy()
        base = np.full(len(val), train["target_value"].mean())
        fitted = fit_logistic(train, FEATURE_SET)
        learned = fitted.predict_proba(val)
        for variant, pred in [("T0_BASE_RATE", base), ("T0_INTAKE_LOGISTIC", learned)]:
            m = metric_bundle(val["target_value"].astype(int).to_numpy(), pred)
            rows.append({"variant": variant, "fold": fold["id"],
                         "train_n": len(train), "validation_n": len(val), **m})

    out = HERE / "metrics"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "canonical_python_fold_metrics.csv", index=False)


if __name__ == "__main__":
    main()
