from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

HERE = Path(__file__).resolve().parent
ASSESSMENT_ROOT = HERE.parent
ABT_DIR = ASSESSMENT_ROOT / "abt"
if str(ABT_DIR) not in sys.path:
    sys.path.insert(0, str(ABT_DIR))

from _common import read_raw
from build_t1 import build_t1
from build_t2 import build_t2
from build_inventory_candidates import build_inventory_candidates


DEVELOPMENT_END = pd.Timestamp("2026-05-01T00:00:00Z")
CALIBRATION_END = pd.Timestamp("2026-06-01T00:00:00Z")
HOLDOUT_END = pd.Timestamp("2026-07-01T00:00:00Z")

PHYSICAL_COLUMNS = [
    "inventory_natural_light",
    "inventory_luminaires",
    "inventory_charging_ports",
    "inventory_security_type",
    "inventory_floor_level",
    "inventory_elevators",
    "inventory_vertical_height_m",
    "inventory_parking_spaces",
    "inventory_building_status",
    "inventory_floor_material",
    "inventory_amenities",
]


def _to_pandas(df: pl.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(df.to_dicts())


def _safe_div(numer: pd.Series, denom: pd.Series) -> pd.Series:
    out = numer.astype(float) / denom.astype(float)
    return out.where(denom.notna() & denom.ne(0))


def _budget_state(
    applicable: pd.Series,
    lower: pd.Series,
    upper: pd.Series | None = None,
) -> pd.Series:
    if upper is None:
        observed = lower.notna()
        return pd.Series(
            np.select(
                [~applicable, observed],
                ["NOT_APPLICABLE", "OBSERVED"],
                default="UNKNOWN",
            ),
            index=lower.index,
            dtype="object",
        )
    both = lower.notna() & upper.notna()
    any_one = lower.notna() | upper.notna()
    return pd.Series(
        np.select(
            [~applicable, both, any_one],
            ["NOT_APPLICABLE", "OBSERVED", "PARTIAL"],
            default="UNKNOWN",
        ),
        index=lower.index,
        dtype="object",
    )


def _interval_distance(value: pd.Series, lower: pd.Series, upper: pd.Series) -> pd.Series:
    midpoint = (lower + upper) / 2.0
    width_scale = midpoint.abs().where(midpoint.abs().gt(0), 1.0)
    below = (lower - value).clip(lower=0)
    above = (value - upper).clip(lower=0)
    distance = below + above
    return (distance / width_scale).where(value.notna() & lower.notna() & upper.notna())


def _within_interval(value: pd.Series, lower: pd.Series, upper: pd.Series) -> pd.Series:
    known = value.notna() & lower.notna() & upper.notna()
    out = pd.Series(pd.NA, index=value.index, dtype="boolean")
    out.loc[known] = value.loc[known].between(lower.loc[known], upper.loc[known], inclusive="both")
    return out


def _completeness(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    rent_app = frame["search_modality"].isin(["rent", "both"])
    sale_app = frame["search_modality"].isin(["sale", "both"])

    intake_base = [
        "user_type",
        "company_size",
        "industry",
        "search_sector",
        "search_modality",
        "target_area_sqm",
        "preferred_state",
        "preferred_municipality",
        "preferred_corridor",
        "source",
    ]
    intake_num = frame[intake_base].notna().sum(axis=1).astype(float)
    intake_den = pd.Series(float(len(intake_base)), index=frame.index)
    intake_num += (
        rent_app
        & frame[["min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly"]]
        .notna()
        .any(axis=1)
    ).astype(float)
    intake_num += (
        sale_app
        & frame[["min_budget_mxn_sale_total", "max_budget_mxn_sale_total"]]
        .notna()
        .any(axis=1)
    ).astype(float)
    intake_den += rent_app.astype(float) + sale_app.astype(float)

    inquiry_base = ["channel", "message_length", "requested_area_sqm", "asked_visit", "urgency_days"]
    inquiry_num = frame[inquiry_base].notna().sum(axis=1).astype(float)
    inquiry_den = pd.Series(float(len(inquiry_base)), index=frame.index)
    inquiry_num += (rent_app & frame["requested_budget_mxn_rent_monthly"].notna()).astype(float)
    inquiry_num += (sale_app & frame["requested_budget_mxn_sale_total"].notna()).astype(float)
    inquiry_den += rent_app.astype(float) + sale_app.astype(float)

    return intake_num / intake_den, inquiry_num / inquiry_den


def add_t1_deterministic_features(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    df["score_time"] = pd.to_datetime(df["score_time"], utc=True)
    rent_app = df["search_modality"].isin(["rent", "both"])
    sale_app = df["search_modality"].isin(["sale", "both"])

    df["rent_budget_applicable"] = rent_app
    df["sale_budget_applicable"] = sale_app
    df["intake_rent_budget_state"] = _budget_state(
        rent_app,
        df["min_budget_mxn_rent_monthly"],
        df["max_budget_mxn_rent_monthly"],
    )
    df["intake_sale_budget_state"] = _budget_state(
        sale_app,
        df["min_budget_mxn_sale_total"],
        df["max_budget_mxn_sale_total"],
    )
    df["inquiry_rent_budget_state"] = _budget_state(
        rent_app, df["requested_budget_mxn_rent_monthly"]
    )
    df["inquiry_sale_budget_state"] = _budget_state(
        sale_app, df["requested_budget_mxn_sale_total"]
    )

    df["intake_rent_budget_midpoint"] = (
        df["min_budget_mxn_rent_monthly"] + df["max_budget_mxn_rent_monthly"]
    ) / 2.0
    df["intake_sale_budget_midpoint"] = (
        df["min_budget_mxn_sale_total"] + df["max_budget_mxn_sale_total"]
    ) / 2.0
    df["intake_rent_budget_width"] = (
        df["max_budget_mxn_rent_monthly"] - df["min_budget_mxn_rent_monthly"]
    )
    df["intake_sale_budget_width"] = (
        df["max_budget_mxn_sale_total"] - df["min_budget_mxn_sale_total"]
    )

    rent_ok = (
        ~rent_app
        | df["min_budget_mxn_rent_monthly"].isna()
        | df["max_budget_mxn_rent_monthly"].isna()
        | (df["min_budget_mxn_rent_monthly"] <= df["max_budget_mxn_rent_monthly"])
    )
    sale_ok = (
        ~sale_app
        | df["min_budget_mxn_sale_total"].isna()
        | df["max_budget_mxn_sale_total"].isna()
        | (df["min_budget_mxn_sale_total"] <= df["max_budget_mxn_sale_total"])
    )
    df["intake_budget_bounds_consistent"] = rent_ok & sale_ok

    df["intake_geography_specificity"] = (
        df[["preferred_state", "preferred_municipality", "preferred_corridor"]]
        .notna()
        .sum(axis=1)
    )
    intake_complete, inquiry_complete = _completeness(df)
    df["intake_completeness_rate"] = intake_complete
    df["inquiry_completeness_rate"] = inquiry_complete

    df["intake_constraint_count"] = (
        df[["target_area_sqm", "preferred_state", "preferred_municipality", "preferred_corridor"]]
        .notna()
        .sum(axis=1)
        + (
            rent_app
            & df[["min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly"]]
            .notna()
            .any(axis=1)
        ).astype(int)
        + (
            sale_app
            & df[["min_budget_mxn_sale_total", "max_budget_mxn_sale_total"]]
            .notna()
            .any(axis=1)
        ).astype(int)
    )
    df["log1p_target_area_sqm"] = np.log1p(df["target_area_sqm"].clip(lower=0))
    df["urgency_not_stated"] = df["urgency_days"].isna()
    df["log1p_message_length"] = np.log1p(df["message_length"].clip(lower=0))
    df["log1p_requested_area_sqm"] = np.log1p(df["requested_area_sqm"].clip(lower=0))

    df["requested_to_target_area_ratio"] = _safe_div(
        df["requested_area_sqm"], df["target_area_sqm"]
    )
    df["requested_target_area_gap_abs"] = (
        df["requested_area_sqm"] - df["target_area_sqm"]
    ).abs()
    df["requested_target_area_gap_log1p"] = np.log1p(
        df["requested_target_area_gap_abs"].clip(lower=0)
    )
    ratio = df["requested_to_target_area_ratio"]
    df["requested_area_direction"] = np.select(
        [ratio.lt(0.95), ratio.gt(1.05)],
        ["LOWER", "HIGHER"],
        default="SAME",
    )

    df["rent_requested_within_intake_interval"] = _within_interval(
        df["requested_budget_mxn_rent_monthly"],
        df["min_budget_mxn_rent_monthly"],
        df["max_budget_mxn_rent_monthly"],
    )
    df["sale_requested_within_intake_interval"] = _within_interval(
        df["requested_budget_mxn_sale_total"],
        df["min_budget_mxn_sale_total"],
        df["max_budget_mxn_sale_total"],
    )
    df["rent_budget_refinement_ratio"] = _safe_div(
        df["requested_budget_mxn_rent_monthly"], df["intake_rent_budget_midpoint"]
    )
    df["sale_budget_refinement_ratio"] = _safe_div(
        df["requested_budget_mxn_sale_total"], df["intake_sale_budget_midpoint"]
    )
    df["rent_budget_interval_distance"] = _interval_distance(
        df["requested_budget_mxn_rent_monthly"],
        df["min_budget_mxn_rent_monthly"],
        df["max_budget_mxn_rent_monthly"],
    )
    df["sale_budget_interval_distance"] = _interval_distance(
        df["requested_budget_mxn_sale_total"],
        df["min_budget_mxn_sale_total"],
        df["max_budget_mxn_sale_total"],
    )

    df["budget_modality_consistent"] = np.select(
        [
            df["search_modality"].eq("rent"),
            df["search_modality"].eq("sale"),
            df["search_modality"].eq("both"),
        ],
        [
            df["requested_budget_mxn_sale_total"].isna(),
            df["requested_budget_mxn_rent_monthly"].isna(),
            df[
                [
                    "requested_budget_mxn_rent_monthly",
                    "requested_budget_mxn_sale_total",
                ]
            ]
            .notna()
            .any(axis=1),
        ],
        default=False,
    ).astype(bool)
    df["completeness_delta_t1_t0"] = (
        df["inquiry_completeness_rate"] - df["intake_completeness_rate"]
    )

    material_area_change = (
        df["requested_to_target_area_ratio"].sub(1).abs().gt(0.10).fillna(False)
    )
    rent_change = (
        rent_app
        & df["rent_requested_within_intake_interval"].eq(False).fillna(False)
    )
    sale_change = (
        sale_app
        & df["sale_requested_within_intake_interval"].eq(False).fillna(False)
    )
    df["need_change_count"] = (
        material_area_change.astype(int)
        + rent_change.astype(int)
        + sale_change.astype(int)
    )

    if "audit_current_spot_created_at" in df:
        created = pd.to_datetime(df["audit_current_spot_created_at"], utc=True)
        df["first_inquiry_lag_days"] = np.nan
        # Lead created_at is intentionally not present in the P4 T1 output.
        # This clock is materialized only by the dedicated EDA path, not core FE.

    return df


def _history_stats(values: list[float]) -> tuple[float, float, float, float]:
    arr = np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    if arr.size == 0:
        return (np.nan, np.nan, np.nan, np.nan)
    last = float(arr[-1])
    avg = float(arr.mean())
    std = float(arr.std(ddof=1)) if arr.size >= 2 else 0.0
    trend = float((arr[-1] - arr[0]) / (arr.size - 1)) if arr.size >= 2 else np.nan
    return last, avg, std, trend


def build_t2_trajectory(repo_root: Path) -> pd.DataFrame:
    inquiry_cols = [
        "inquiry_id",
        "lead_id",
        "spot_id",
        "inquiry_at",
        "channel",
        "message_length",
        "requested_area_sqm",
        "requested_budget_mxn_rent_monthly",
        "requested_budget_mxn_sale_total",
        "urgency_days",
        "asked_visit",
    ]
    raw = _to_pandas(read_raw(repo_root, "inquiries").select(inquiry_cols))
    leads = _to_pandas(read_raw(repo_root, "leads").select(["lead_id", "search_modality"]))
    lead_mode = dict(zip(leads["lead_id"], leads["search_modality"]))
    raw["inquiry_at"] = pd.to_datetime(raw["inquiry_at"], utc=True)
    raw = raw.sort_values(["lead_id", "inquiry_at", "inquiry_id"]).reset_index(drop=True)

    output: list[dict] = []
    for lead_id, grp in raw.groupby("lead_id", sort=False):
        history_times: list[pd.Timestamp] = []
        history_gaps: list[float] = []
        channels: list[str] = []
        spots: list[int] = []
        areas: list[float] = []
        rent_budgets: list[float] = []
        sale_budgets: list[float] = []
        urgencies: list[float] = []
        constraints: list[float] = []
        last_time: pd.Timestamp | None = None
        mode = lead_mode[lead_id]

        for score_time, batch in grp.groupby("inquiry_at", sort=True):
            # Every row in a same-timestamp batch sees the same strict-prior state.
            for row in batch.sort_values("inquiry_id").to_dict("records"):
                area_last, area_mean, area_std, area_trend = _history_stats(areas)
                rent_last, rent_mean, rent_std, rent_trend = _history_stats(rent_budgets)
                sale_last, sale_mean, sale_std, sale_trend = _history_stats(sale_budgets)
                urg_last, urg_mean, urg_std, urg_trend = _history_stats(urgencies)
                con_last, con_mean, con_std, con_trend = _history_stats(constraints)

                prior_30d = sum(
                    t >= score_time - pd.Timedelta(days=30) for t in history_times
                )
                same_channel_rate = (
                    sum(c == row["channel"] for c in channels) / len(channels)
                    if channels
                    else np.nan
                )
                current_spot_prior_count = spots.count(row["spot_id"])
                current_constraint = (
                    int(pd.notna(row["requested_area_sqm"]))
                    + int(pd.notna(row["urgency_days"]))
                    + int(bool(row["asked_visit"]))
                    + int(
                        mode in {"rent", "both"}
                        and pd.notna(row["requested_budget_mxn_rent_monthly"])
                    )
                    + int(
                        mode in {"sale", "both"}
                        and pd.notna(row["requested_budget_mxn_sale_total"])
                    )
                )

                output.append(
                    {
                        "inquiry_id": row["inquiry_id"],
                        "t2_prior_inquiry_count": len(history_times),
                        "t2_time_since_previous_inquiry_days": (
                            (score_time - last_time).total_seconds() / 86400.0
                            if last_time is not None
                            else np.nan
                        ),
                        "t2_hist_gap_mean_days": (
                            float(np.mean(history_gaps)) if history_gaps else np.nan
                        ),
                        "t2_hist_gap_median_days": (
                            float(np.median(history_gaps)) if history_gaps else np.nan
                        ),
                        "t2_inquiry_velocity_30d": prior_30d / 30.0,
                        "t2_prior_unique_channels": len(set(channels)),
                        "t2_prior_same_channel_rate": same_channel_rate,
                        "t2_hist_area_last": area_last,
                        "t2_hist_area_mean": area_mean,
                        "t2_hist_area_std": area_std,
                        "t2_hist_area_trend_per_step": area_trend,
                        "t2_current_to_hist_area_ratio": (
                            row["requested_area_sqm"] / area_mean
                            if pd.notna(row["requested_area_sqm"])
                            and pd.notna(area_mean)
                            and area_mean != 0
                            else np.nan
                        ),
                        "t2_hist_rent_budget_last": rent_last,
                        "t2_hist_rent_budget_mean": rent_mean,
                        "t2_hist_rent_budget_std": rent_std,
                        "t2_hist_rent_budget_trend_per_step": rent_trend,
                        "t2_current_to_hist_rent_budget_ratio": (
                            row["requested_budget_mxn_rent_monthly"] / rent_mean
                            if pd.notna(row["requested_budget_mxn_rent_monthly"])
                            and pd.notna(rent_mean)
                            and rent_mean != 0
                            else np.nan
                        ),
                        "t2_hist_sale_budget_last": sale_last,
                        "t2_hist_sale_budget_mean": sale_mean,
                        "t2_hist_sale_budget_std": sale_std,
                        "t2_hist_sale_budget_trend_per_step": sale_trend,
                        "t2_current_to_hist_sale_budget_ratio": (
                            row["requested_budget_mxn_sale_total"] / sale_mean
                            if pd.notna(row["requested_budget_mxn_sale_total"])
                            and pd.notna(sale_mean)
                            and sale_mean != 0
                            else np.nan
                        ),
                        "t2_hist_urgency_last": urg_last,
                        "t2_hist_urgency_mean": urg_mean,
                        "t2_hist_urgency_std": urg_std,
                        "t2_hist_urgency_trend_per_step": urg_trend,
                        "t2_current_vs_hist_urgency_delta": (
                            row["urgency_days"] - urg_mean
                            if pd.notna(row["urgency_days"]) and pd.notna(urg_mean)
                            else np.nan
                        ),
                        "t2_prior_unique_spots": len(set(spots)),
                        "t2_current_spot_prior_count": current_spot_prior_count,
                        "t2_current_spot_revisit_flag": current_spot_prior_count > 0,
                        "t2_hist_constraint_count_mean": con_mean,
                        "t2_hist_constraint_count_std": con_std,
                        "t2_current_vs_hist_constraint_delta": (
                            current_constraint - con_mean
                            if pd.notna(con_mean)
                            else np.nan
                        ),
                        "_strict_prior_max_time": max(history_times) if history_times else pd.NaT,
                    }
                )

            # Only after all same-time rows are scored do they become history.
            for row in batch.sort_values("inquiry_id").to_dict("records"):
                if last_time is not None:
                    history_gaps.append((score_time - last_time).total_seconds() / 86400.0)
                history_times.append(score_time)
                last_time = score_time
                channels.append(row["channel"])
                spots.append(row["spot_id"])
                if pd.notna(row["requested_area_sqm"]):
                    areas.append(float(row["requested_area_sqm"]))
                if pd.notna(row["requested_budget_mxn_rent_monthly"]):
                    rent_budgets.append(float(row["requested_budget_mxn_rent_monthly"]))
                if pd.notna(row["requested_budget_mxn_sale_total"]):
                    sale_budgets.append(float(row["requested_budget_mxn_sale_total"]))
                if pd.notna(row["urgency_days"]):
                    urgencies.append(float(row["urgency_days"]))
                constraints.append(
                    int(pd.notna(row["requested_area_sqm"]))
                    + int(pd.notna(row["urgency_days"]))
                    + int(bool(row["asked_visit"]))
                    + int(
                        mode in {"rent", "both"}
                        and pd.notna(row["requested_budget_mxn_rent_monthly"])
                    )
                    + int(
                        mode in {"sale", "both"}
                        and pd.notna(row["requested_budget_mxn_sale_total"])
                    )
                )

    return pd.DataFrame(output)


def build_selected_spot_context(
    inventory_audit: pl.DataFrame,
    t1_features: pd.DataFrame,
) -> pd.DataFrame:
    inv = _to_pandas(
        inventory_audit.filter(
            (pl.col("stage") == "T1") & pl.col("matching_is_observed_current_spot")
        )
    )
    if inv.empty:
        return pd.DataFrame({"score_id": t1_features["score_id"]})

    pref = t1_features[
        ["score_id", "preferred_municipality", "preferred_corridor"]
    ].drop_duplicates("score_id")
    inv = inv.merge(pref, on="score_id", how="left", validate="many_to_one")
    inv["selected_spot_area_ratio"] = inv["matching_area_ratio"]
    inv["selected_spot_area_gap_sqm"] = inv["matching_area_gap_sqm"]
    inv["selected_spot_modality_compatible"] = inv["matching_modality_compatible"]
    inv["selected_spot_sector_compatible"] = inv["matching_sector_exact"]
    inv["selected_spot_preferred_municipality_match"] = (
        inv["matching_candidate_municipality"] == inv["preferred_municipality"]
    )
    inv["selected_spot_preferred_corridor_match"] = (
        inv["matching_candidate_corridor"] == inv["preferred_corridor"]
    )
    inv["selected_spot_availability_known"] = inv["availability_known"]
    inv["selected_spot_is_available_asof"] = inv["is_available_asof"]
    inv["selected_spot_snapshot_age_days"] = inv["snapshot_age_days"]
    inv["selected_spot_physical_attribute_completeness"] = (
        inv[PHYSICAL_COLUMNS].notna().mean(axis=1)
    )
    cols = ["score_id"] + [
        c for c in inv.columns if c.startswith("selected_spot_")
    ]
    out = inv[cols].copy()
    if out["score_id"].duplicated().any():
        raise AssertionError("Selected Spot context must be one row per T1 score_id")
    return out


def build_inventory_feature_table(
    repo_root: Path,
    inventory_audit: pl.DataFrame,
) -> pl.DataFrame:
    leads = read_raw(repo_root, "leads").select(
        "lead_id", "preferred_municipality", "preferred_corridor"
    )
    out = (
        inventory_audit.join(leads, on="lead_id", how="left", validate="m:1")
        .with_columns(
            pl.col("matching_area_ratio").alias("requested_to_spot_area_ratio"),
            pl.col("matching_area_gap_sqm").alias("candidate_area_gap_sqm"),
            pl.col("matching_modality_compatible").alias("candidate_modality_compatible"),
            pl.col("matching_sector_exact").alias("candidate_sector_compatible"),
            (
                pl.col("matching_candidate_municipality")
                == pl.col("preferred_municipality")
            ).alias("preferred_municipality_match"),
            (
                pl.col("matching_candidate_corridor") == pl.col("preferred_corridor")
            ).alias("preferred_corridor_match"),
            pl.col("matching_fallback_tier").alias("geographic_relaxation_level"),
            pl.col("matching_area_ratio")
            .is_between(0.80, 1.25, closed="both")
            .fill_null(False)
            .alias("physical_space_compatibility"),
        )
        .with_columns(
            pl.len().over("score_id").alias("inventory_candidate_count")
        )
    )
    return out


def build_feature_artifacts(
    repo_root: Path,
    *,
    scope: str = "development",
) -> dict:
    out_dir = ASSESSMENT_ROOT / "features" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    scope_cutoffs = {
        "development": DEVELOPMENT_END,
        "calibration_inclusive": CALIBRATION_END,
        "holdout_inclusive": HOLDOUT_END,
    }
    if scope not in scope_cutoffs:
        raise ValueError(f"Unknown feature-build scope: {scope}")
    max_time = scope_cutoffs[scope]
    cutoff = max_time.to_pydatetime()
    t1_audit_pl, _ = build_t1(
        repo_root, max_score_time_exclusive=cutoff
    )
    t2_audit_pl, t2_model_pl = build_t2(
        repo_root, max_score_time_exclusive=cutoff
    )
    inventory_audit, _ = build_inventory_candidates(
        repo_root, max_score_time_exclusive=cutoff
    )

    t1 = add_t1_deterministic_features(_to_pandas(t1_audit_pl))
    t1["score_time"] = pd.to_datetime(t1["score_time"], utc=True)
    t1 = t1.loc[t1["score_time"] < max_time].copy()

    selected = build_selected_spot_context(inventory_audit, t1)
    t1_with_spot = t1.merge(selected, on="score_id", how="left", validate="one_to_one")

    traj = build_t2_trajectory(repo_root)
    t2 = _to_pandas(t2_audit_pl)
    t2["score_time"] = pd.to_datetime(t2["score_time"], utc=True)
    t2 = t2.merge(traj, on="inquiry_id", how="left", validate="one_to_one")
    t2 = t2.loc[t2["score_time"] < max_time].copy()

    if (
        t2["_strict_prior_max_time"].notna()
        & (pd.to_datetime(t2["_strict_prior_max_time"], utc=True) >= t2["score_time"])
    ).any():
        raise AssertionError("T2 trajectory includes same-time/future history")

    t2_valid_ids = set(t2_model_pl["inquiry_id"].to_list())
    t2["model_ready"] = t2["inquiry_id"].isin(t2_valid_ids)

    inventory = build_inventory_feature_table(repo_root, inventory_audit)
    inventory = inventory.filter(
        pl.col("score_time")
        < pl.lit(max_time.to_pydatetime())
    )

    t1_path = out_dir / f"t1_features_{scope}_audit.parquet"
    t1_spot_path = out_dir / f"t1_features_{scope}_with_selected_spot_challenger.parquet"
    t2_path = out_dir / f"t2_features_{scope}_audit.parquet"
    inv_path = out_dir / f"inventory_features_{scope}.parquet"
    pl.DataFrame(t1.to_dict("list")).write_parquet(t1_path)
    pl.DataFrame(t1_with_spot.to_dict("list")).write_parquet(t1_spot_path)
    pl.DataFrame(t2.drop(columns=["_strict_prior_max_time"]).to_dict("list")).write_parquet(t2_path)
    inventory.write_parquet(inv_path)

    manifest = {
        "version": "FEATURE_ARTIFACTS_V1",
        "scope": scope,
        "procedural_holdout_included": scope == "holdout_inclusive",
        "max_score_time_exclusive": str(max_time),
        "t1_rows": len(t1),
        "t2_rows": len(t2),
        "inventory_rows": inventory.height,
        "response_history_feature_used": False,
        "market_context_used": False,
        "spot_price_used": False,
        "t2_strict_prior_gate": True,
        "artifacts": [
            t1_path.name,
            t1_spot_path.name,
            t2_path.name,
            inv_path.name,
        ],
    }
    (out_dir / f"feature_manifest_{scope}.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope",
        choices=["development", "calibration_inclusive", "holdout_inclusive"],
        default="development",
    )
    args = parser.parse_args()
    if args.scope == "holdout_inclusive":
        frozen = ASSESSMENT_ROOT / "models" / "lead_quality" / "FROZEN_MODEL_CONFIG.json"
        if not frozen.exists():
            raise RuntimeError(
                "Procedural holdout is sealed: FROZEN_MODEL_CONFIG.json does not exist"
            )
        payload = json.loads(frozen.read_text())
        if payload.get("status") != "FROZEN":
            raise RuntimeError("Procedural holdout is sealed: model config is not FROZEN")
    repo_root = Path(__file__).resolve().parents[2]
    print(
        json.dumps(
            build_feature_artifacts(repo_root, scope=args.scope),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
