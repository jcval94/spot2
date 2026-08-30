from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from feature_engineering import (
    HORIZON_DAYS,
    STAGES,
    add_history_features,
    add_match_features,
    add_supply_history_features,
    add_target,
    assert_no_blocked_features,
    attach_availability,
    attach_spot_features,
    engineer_inquiry_rows,
    engineer_leads,
    engineer_spots,
    feature_columns_for_stage,
    prepare_inquiries,
    validate_raw_tables,
)


def read_inputs(repo_root: Path):
    p = repo_root / "data" / "candidate" / "csv"
    leads = pd.read_csv(p / "leads.csv", parse_dates=["created_at"])
    spots = pd.read_csv(p / "spots.csv", parse_dates=["created_at"])
    attrs = pd.read_csv(p / "spot_attributes.csv")
    inquiries = pd.read_csv(p / "inquiries.csv", parse_dates=["inquiry_at"])
    availability = pd.read_csv(p / "availability_snapshot.csv", parse_dates=["snapshot_date"])
    market = pd.read_csv(p / "market_context.csv", parse_dates=["month"])
    return leads, spots, attrs, inquiries, availability, market


def build_all(repo_root: Path):
    leads, spots, attrs, inquiries, availability, market = read_inputs(repo_root)
    validate_raw_tables(leads, spots, attrs, inquiries, availability)

    leads_fe = engineer_leads(leads)
    inquiries_fe = add_supply_history_features(
        add_history_features(prepare_inquiries(inquiries)),
        spots,
    )
    spots_fe = engineer_spots(spots, attrs)

    # T0: one row per lead at creation. No spot/inquiry context is invented.
    t0 = leads_fe.copy()
    t0["stage_id"] = 0
    t0["stage"] = STAGES[0]
    t0["score_time"] = t0["created_at"]
    t0["row_id"] = np.arange(len(t0))
    t0 = add_target(t0, inquiries_fe, HORIZON_DAYS)

    # T1/T2: every inquiry is a scoring point until a scheduled visit has already occurred.
    dyn = inquiries_fe.merge(
        leads_fe,
        on="lead_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_lead"),
    )
    first_conversion = (
        inquiries_fe[
            inquiries_fe["broker_response"].eq("scheduled_visit")
            & inquiries_fe["response_event_at"].notna()
        ]
        .groupby("lead_id")["response_event_at"]
        .min()
        .rename("first_conversion_at")
    )
    dyn = dyn.merge(first_conversion, on="lead_id", how="left")
    dyn = dyn[
        dyn["first_conversion_at"].isna()
        | (dyn["inquiry_at"] < dyn["first_conversion_at"])
    ].copy()
    dyn["stage_id"] = np.where(dyn["inquiry_number"].eq(1), 1, 2)
    dyn["stage"] = dyn["stage_id"].map(STAGES)
    dyn["score_time"] = dyn["inquiry_at"]
    dyn["row_id"] = np.arange(len(dyn))

    dyn = engineer_inquiry_rows(dyn)
    dyn = attach_spot_features(dyn, spots_fe)
    dyn = attach_availability(dyn, availability)
    dyn = add_match_features(dyn)
    dyn = add_target(dyn, inquiries_fe, HORIZON_DAYS)

    # Training-ready populations: complete 30-day observation window only.
    t0_ready = t0[t0["is_right_censored"].eq(0)].copy()
    t1_ready = dyn[
        dyn["stage_id"].eq(1) & dyn["is_right_censored"].eq(0)
    ].copy()
    t2_ready = dyn[
        dyn["stage_id"].eq(2) & dyn["is_right_censored"].eq(0)
    ].copy()

    # Stable chronological lead-cohort split shared by all stages.
    lead_order = (
        leads_fe[["lead_id", "created_at"]]
        .sort_values(["created_at", "lead_id"])
        .reset_index(drop=True)
    )
    n = len(lead_order)
    a, b = int(n * 0.70), int(n * 0.85)
    lead_order["split"] = "test"
    lead_order.loc[: a - 1, "split"] = "train"
    lead_order.loc[a : b - 1, "split"] = "val"
    split_map = lead_order.set_index("lead_id")["split"]

    for d in (t0_ready, t1_ready, t2_ready):
        d["split"] = d["lead_id"].map(split_map)

    feature_sets = {
        0: feature_columns_for_stage(0),
        1: feature_columns_for_stage(1),
        2: feature_columns_for_stage(2),
    }
    for cols in feature_sets.values():
        assert_no_blocked_features(cols)

    return {"T0": t0_ready, "T1": t1_ready, "T2": t2_ready}, feature_sets, market


def project_abt(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    meta = [
        "lead_id",
        "stage_id",
        "stage",
        "score_time",
        "split",
        "target_scheduled_visit_30d",
        "observation_end",
        "censor_cutoff",
    ]
    for optional in ["inquiry_id", "spot_id", "broker_id", "inquiry_number"]:
        if optional in df.columns:
            meta.append(optional)

    missing = [c for c in features if c not in df.columns]
    if missing:
        raise KeyError(f"Missing engineered columns: {missing}")
    return df[meta + features].copy()


def write_outputs(
    abts: dict[str, pd.DataFrame],
    feature_sets: dict[int, list[str]],
    out: Path,
):
    out.mkdir(parents=True, exist_ok=True)
    mapping = {"T0": 0, "T1": 1, "T2": 2}
    summary = []

    for name, df in abts.items():
        projected = project_abt(df, feature_sets[mapping[name]])
        projected.to_parquet(out / f"abt_{name.lower()}.parquet", index=False)
        projected.head(200).to_csv(
            out / f"abt_{name.lower()}_sample.csv",
            index=False,
        )
        summary.append(
            {
                "abt": name,
                "rows": len(projected),
                "features": len(feature_sets[mapping[name]]),
                "positive_rate": projected["target_scheduled_visit_30d"].mean(),
                "train": (projected["split"] == "train").sum(),
                "val": (projected["split"] == "val").sum(),
                "test": (projected["split"] == "test").sum(),
            }
        )

    pd.DataFrame(summary).to_csv(out / "abt_summary.csv", index=False)
    with (out / "feature_sets.txt").open("w", encoding="utf-8") as f:
        for stage_id, cols in feature_sets.items():
            f.write(f"[{STAGES[stage_id]}]\n")
            f.write("\n".join(cols) + "\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
    )
    args = ap.parse_args()

    abts, feature_sets, _market = build_all(args.repo_root)
    write_outputs(abts, feature_sets, args.output_dir)
    print(pd.read_csv(args.output_dir / "abt_summary.csv").to_string(index=False))


if __name__ == "__main__":
    main()
