from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HORIZON_DAYS = 30

BLUE = "#2563EB"
BLUE_LIGHT = "#93C5FD"
GOLD = "#D4A017"
GREY = "#6B7280"
LIGHT_GREY = "#E5E7EB"
DARK = "#111827"


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)


def _style_axis(ax: plt.Axes, title: str, subtitle: str = "") -> None:
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=DARK, pad=18)
    if subtitle:
        ax.text(
            0,
            1.02,
            subtitle,
            transform=ax.transAxes,
            fontsize=9,
            color=GREY,
            va="bottom",
        )
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=LIGHT_GREY, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)


def _bar(
    labels: list[str],
    values: list[float],
    path: Path,
    title: str,
    subtitle: str,
    percent: bool = False,
    horizontal: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(labels))
    if horizontal:
        bars = ax.barh(x, values, color=BLUE)
        ax.set_yticks(x, labels)
        ax.invert_yaxis()
        for bar, value in zip(bars, values):
            text = f"{value:.1%}" if percent else f"{value:,.2f}"
            ax.text(value, bar.get_y() + bar.get_height() / 2, f"  {text}", va="center", fontsize=9)
        ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8, alpha=0.8)
        ax.grid(axis="y", visible=False)
    else:
        bars = ax.bar(x, values, color=BLUE)
        ax.set_xticks(x, labels, rotation=25, ha="right")
        for bar, value in zip(bars, values):
            text = f"{value:.1%}" if percent else f"{value:,.0f}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                text,
                ha="center",
                va="bottom",
                fontsize=9,
            )
    if percent:
        limit = max(values) * 1.25 if values else 1
        if horizontal:
            ax.set_xlim(0, limit)
            ax.xaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
        else:
            ax.set_ylim(0, limit)
            ax.yaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
    _style_axis(ax, title, subtitle)
    if horizontal:
        ax.grid(axis="x", color=LIGHT_GREY, linewidth=0.8, alpha=0.8)
        ax.grid(axis="y", visible=False)
    fig.tight_layout()
    _save(fig, path)


def _grouped_bar(
    labels: list[str],
    series: dict[str, list[float]],
    path: Path,
    title: str,
    subtitle: str,
    percent: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(labels))
    width = 0.36
    palette = [BLUE, GOLD]
    offsets = np.linspace(-width / 2, width / 2, len(series))
    for idx, ((name, values), offset) in enumerate(zip(series.items(), offsets)):
        bars = ax.bar(x + offset, values, width, label=name, color=palette[idx % len(palette)])
        for bar, value in zip(bars, values):
            text = f"{value:.1%}" if percent else f"{value:,.0f}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                text,
                ha="center",
                va="bottom",
                fontsize=8,
            )
    ax.set_xticks(x, labels)
    if percent:
        ax.yaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
        ymax = max(max(v) for v in series.values())
        ax.set_ylim(0, ymax * 1.25)
    ax.legend(frameon=False, loc="upper right")
    _style_axis(ax, title, subtitle)
    fig.tight_layout()
    _save(fig, path)


def _line(
    labels: list[str],
    values: list[float],
    path: Path,
    title: str,
    subtitle: str,
    percent: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    x = np.arange(len(labels))
    ax.plot(x, values, marker="o", linewidth=2, color=BLUE)
    ax.set_xticks(x, labels, rotation=45, ha="right")
    if percent:
        ax.yaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
    _style_axis(ax, title, subtitle)
    fig.tight_layout()
    _save(fig, path)


def load_data(repo_root: Path) -> dict[str, pd.DataFrame]:
    base = repo_root / "data" / "candidate" / "csv"
    return {
        "leads": pd.read_csv(base / "leads.csv", parse_dates=["created_at"]),
        "inquiries": pd.read_csv(base / "inquiries.csv", parse_dates=["inquiry_at"]),
        "spots": pd.read_csv(base / "spots.csv", parse_dates=["created_at"]),
        "spot_attributes": pd.read_csv(base / "spot_attributes.csv"),
        "market_context": pd.read_csv(base / "market_context.csv", parse_dates=["month"]),
        "availability_snapshot": pd.read_csv(
            base / "availability_snapshot.csv", parse_dates=["snapshot_date"]
        ),
    }


def _profile_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    keys = {
        "leads": "lead_id",
        "inquiries": "inquiry_id",
        "spots": "spot_id",
        "spot_attributes": "spot_id",
        "availability_snapshot": "snapshot_id",
    }
    rows: list[dict[str, Any]] = []
    for name, df in data.items():
        row = {
            "table": name,
            "rows": len(df),
            "columns": len(df.columns),
            "primary_key": keys.get(name, ""),
            "pk_duplicates": int(df[keys[name]].duplicated().sum()) if name in keys else np.nan,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def _missingness_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    structural = {
        ("leads", "min_budget_mxn_rent_monthly"): "structural_by_search_modality",
        ("leads", "max_budget_mxn_rent_monthly"): "structural_by_search_modality",
        ("leads", "min_budget_mxn_sale_total"): "structural_by_search_modality",
        ("leads", "max_budget_mxn_sale_total"): "structural_by_search_modality",
        ("inquiries", "requested_budget_mxn_rent_monthly"): "partly_structural_by_modality",
        ("inquiries", "requested_budget_mxn_sale_total"): "partly_structural_by_modality",
        ("spots", "price_sqm_mxn_rent"): "structural_by_modality",
        ("spots", "price_total_mxn_rent"): "structural_by_modality",
        ("spots", "maintenance_cost_mxn"): "structural_by_modality",
        ("spots", "price_sqm_mxn_sale"): "structural_by_modality",
        ("spots", "price_total_mxn_sale"): "structural_by_modality",
    }
    rows = []
    for table, df in data.items():
        for column in df.columns:
            count = int(df[column].isna().sum())
            rows.append(
                {
                    "table": table,
                    "column": column,
                    "missing_count": count,
                    "missing_rate": count / len(df) if len(df) else np.nan,
                    "interpretation": structural.get((table, column), "ordinary_or_domain_specific"),
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["missing_rate", "table", "column"], ascending=[False, True, True]
    )


def _success_lookup(
    leads: pd.DataFrame, inquiries: pd.DataFrame
) -> tuple[pd.Timestamp, dict[Any, pd.DataFrame]]:
    max_observed = inquiries["inquiry_at"].max()
    censor_cutoff = max_observed - pd.Timedelta(days=HORIZON_DAYS)
    by_lead = {
        lead_id: group.sort_values(["inquiry_at", "inquiry_id"]).copy()
        for lead_id, group in inquiries.groupby("lead_id")
    }
    return censor_cutoff, by_lead


def _has_future_visit(group: pd.DataFrame, scoring_time: pd.Timestamp) -> bool:
    if group is None or group.empty:
        return False
    mask = (
        group["broker_response"].eq("scheduled_visit")
        & group["inquiry_at"].between(
            scoring_time,
            scoring_time + pd.Timedelta(days=HORIZON_DAYS),
            inclusive="both",
        )
    )
    return bool(mask.any())


def _had_prior_visit(group: pd.DataFrame, scoring_time: pd.Timestamp) -> bool:
    if group is None or group.empty:
        return False
    return bool(
        (
            group["broker_response"].eq("scheduled_visit")
            & group["inquiry_at"].lt(scoring_time)
        ).any()
    )


def build_stage_table(
    leads: pd.DataFrame, inquiries: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.Timestamp]:
    censor_cutoff, by_lead = _success_lookup(leads, inquiries)
    stage_frames: dict[str, pd.DataFrame] = {}
    stage_rows: list[dict[str, Any]] = []

    definitions = [("T0", None), ("T1", 0), ("T2", 1), ("T3", 2)]
    for stage, inquiry_index in definitions:
        records: list[dict[str, Any]] = []
        for _, lead in leads.iterrows():
            group = by_lead.get(lead["lead_id"])
            if inquiry_index is None:
                scoring_time = lead["created_at"]
                selected_inquiry = None
            else:
                if group is None or len(group) <= inquiry_index:
                    continue
                selected_inquiry = group.iloc[inquiry_index]
                scoring_time = selected_inquiry["inquiry_at"]

            if scoring_time > censor_cutoff:
                continue
            if inquiry_index is not None and inquiry_index >= 1:
                if _had_prior_visit(group, scoring_time):
                    continue

            row = lead.to_dict()
            row["stage"] = stage
            row["scoring_time"] = scoring_time
            row["target_30d"] = int(_has_future_visit(group, scoring_time))
            if selected_inquiry is not None:
                for col in [
                    "inquiry_id",
                    "spot_id",
                    "channel",
                    "message_length",
                    "requested_area_sqm",
                    "requested_budget_mxn_rent_monthly",
                    "requested_budget_mxn_sale_total",
                    "urgency_days",
                    "asked_visit",
                ]:
                    row[col] = selected_inquiry[col]
            records.append(row)

        frame = pd.DataFrame(records)
        stage_frames[stage] = frame
        stage_rows.append(
            {
                "stage": stage,
                "eligible_rows": len(frame),
                "share_of_all_leads": len(frame) / len(leads),
                "proxy_positive_rate": frame["target_30d"].mean() if len(frame) else np.nan,
                "scoring_definition": {
                    "T0": "lead creation",
                    "T1": "first inquiry",
                    "T2": "second inquiry, excluding prior scheduled visit",
                    "T3": "third inquiry, excluding prior scheduled visit",
                }[stage],
            }
        )

    return pd.DataFrame(stage_rows), stage_frames, censor_cutoff


def _segment_rates(frame: pd.DataFrame, columns: list[str], stage: str) -> pd.DataFrame:
    rows = []
    for column in columns:
        if column not in frame.columns:
            continue
        grouped = (
            frame.groupby(column, dropna=False)["target_30d"]
            .agg(["size", "mean"])
            .reset_index()
        )
        for _, row in grouped.iterrows():
            rows.append(
                {
                    "stage": stage,
                    "dimension": column,
                    "segment": row[column],
                    "n": int(row["size"]),
                    "proxy_positive_rate": float(row["mean"]),
                }
            )
    return pd.DataFrame(rows)


def _t1_breakdowns(t1: pd.DataFrame) -> pd.DataFrame:
    frame = t1.copy()
    lag = (frame["scoring_time"] - frame["created_at"]).dt.total_seconds() / 86400
    frame["first_inquiry_lag_bucket"] = pd.cut(
        lag,
        bins=[-np.inf, 1, 3, 7, 30, np.inf],
        labels=["<1d", "1-3d", "3-7d", "7-30d", ">=30d"],
        right=False,
    )
    frame["urgency_bucket"] = pd.cut(
        frame["urgency_days"],
        bins=[-np.inf, 31, 91, 181, np.inf],
        labels=["<=30d", "31-90d", "91-180d", ">180d"],
        right=False,
    ).astype("object")
    frame["urgency_bucket"] = frame["urgency_bucket"].fillna("missing")

    rows = []
    for column in [
        "channel",
        "asked_visit",
        "first_inquiry_lag_bucket",
        "urgency_bucket",
        "search_sector",
        "search_modality",
        "user_type",
    ]:
        grouped = (
            frame.groupby(column, dropna=False)["target_30d"]
            .agg(["size", "mean"])
            .reset_index()
        )
        for _, row in grouped.iterrows():
            rows.append(
                {
                    "dimension": column,
                    "segment": row[column],
                    "n": int(row["size"]),
                    "proxy_positive_rate": float(row["mean"]),
                }
            )
    return pd.DataFrame(rows)


def _join_quality(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    leads = data["leads"]
    inquiries = data["inquiries"]
    spots = data["spots"]
    attrs = data["spot_attributes"]
    availability = data["availability_snapshot"]
    market = data["market_context"]

    lead_ids = set(leads["lead_id"])
    spot_ids = set(spots["spot_id"])

    inquiry_plus = inquiries.merge(
        leads[["lead_id", "created_at", "search_modality"]].rename(
            columns={"created_at": "lead_created_at"}
        ),
        on="lead_id",
        how="left",
    ).merge(
        spots[["spot_id", "created_at", "modality"]].rename(
            columns={"created_at": "spot_created_at"}
        ),
        on="spot_id",
        how="left",
    )
    compatibility = (
        inquiry_plus["search_modality"].eq("both")
        | inquiry_plus["modality"].eq("both")
        | inquiry_plus["search_modality"].eq(inquiry_plus["modality"])
    )

    censor_cutoff = inquiries["inquiry_at"].max() - pd.Timedelta(days=HORIZON_DAYS)
    lead_market = leads[leads["created_at"] <= censor_cutoff].copy()
    lead_market["month"] = lead_market["created_at"].dt.to_period("M").dt.to_timestamp()
    market_keys = market[
        ["state", "municipality", "corridor", "sector", "month"]
    ].drop_duplicates()
    lead_market_join = lead_market.merge(
        market_keys,
        how="left",
        left_on=[
            "preferred_state",
            "preferred_municipality",
            "preferred_corridor",
            "search_sector",
            "month",
        ],
        right_on=["state", "municipality", "corridor", "sector", "month"],
        indicator=True,
    )

    rows = [
        {
            "check": "inquiries -> leads orphan rows",
            "value": int((~inquiries["lead_id"].isin(lead_ids)).sum()),
            "severity": "critical_if_nonzero",
        },
        {
            "check": "inquiries -> spots orphan rows",
            "value": int((~inquiries["spot_id"].isin(spot_ids)).sum()),
            "severity": "critical_if_nonzero",
        },
        {
            "check": "spot_attributes -> spots orphan rows",
            "value": int((~attrs["spot_id"].isin(spot_ids)).sum()),
            "severity": "critical_if_nonzero",
        },
        {
            "check": "availability -> spots orphan rows",
            "value": int((~availability["spot_id"].isin(spot_ids)).sum()),
            "severity": "critical_if_nonzero",
        },
        {
            "check": "inquiries before lead creation",
            "value": int((inquiry_plus["inquiry_at"] < inquiry_plus["lead_created_at"]).sum()),
            "severity": "critical_if_nonzero",
        },
        {
            "check": "inquiries before spot creation",
            "value": int((inquiry_plus["inquiry_at"] < inquiry_plus["spot_created_at"]).sum()),
            "severity": "critical_if_nonzero",
        },
        {
            "check": "inquiry modality incompatibilities",
            "value": int((~compatibility).sum()),
            "severity": "high_if_nonzero",
        },
        {
            "check": "exact lead-market context coverage at lead month",
            "value": float((lead_market_join["_merge"] == "both").mean()),
            "severity": "coverage_not_failure",
        },
    ]
    return pd.DataFrame(rows)


def _availability_asof_t1(
    t1: pd.DataFrame, availability: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    snapshots = availability.sort_values(["spot_id", "snapshot_date"]).copy()
    left = t1[["lead_id", "spot_id", "scoring_time", "target_30d"]].copy()
    left["scoring_date"] = left["scoring_time"].dt.normalize()
    merged = pd.merge_asof(
        left.sort_values("scoring_date"),
        snapshots.sort_values("snapshot_date"),
        left_on="scoring_date",
        right_on="snapshot_date",
        by="spot_id",
        direction="backward",
        allow_exact_matches=True,
    )
    covered = merged[merged["snapshot_id"].notna()].copy()
    rows = []
    for column in ["is_available"]:
        grouped = (
            covered.groupby(column, dropna=False)["target_30d"]
            .agg(["size", "mean"])
            .reset_index()
        )
        for _, row in grouped.iterrows():
            rows.append(
                {
                    "dimension": column,
                    "segment": row[column],
                    "n": int(row["size"]),
                    "proxy_positive_rate": float(row["mean"]),
                }
            )
    return merged, pd.DataFrame(rows)


def _sector_balance(
    leads: pd.DataFrame,
    spots: pd.DataFrame,
    availability: pd.DataFrame,
) -> pd.DataFrame:
    latest = (
        availability.sort_values(["spot_id", "snapshot_date"])
        .drop_duplicates("spot_id", keep="last")
        .merge(spots[["spot_id", "sector_name", "corridor"]], on="spot_id", how="left")
    )
    lead_counts = leads["search_sector"].value_counts()
    spot_counts = spots["sector_name"].value_counts()
    available_counts = latest.loc[latest["is_available"], "sector_name"].value_counts()
    sectors = sorted(set(lead_counts.index) | set(spot_counts.index))
    total_available = int(latest["is_available"].sum())
    rows = []
    for sector in sectors:
        rows.append(
            {
                "sector": sector,
                "leads": int(lead_counts.get(sector, 0)),
                "spots": int(spot_counts.get(sector, 0)),
                "latest_available_spots": int(available_counts.get(sector, 0)),
                "lead_share": lead_counts.get(sector, 0) / len(leads),
                "spot_share": spot_counts.get(sector, 0) / len(spots),
                "latest_available_share": (
                    available_counts.get(sector, 0) / total_available if total_available else np.nan
                ),
                "leads_per_latest_available_spot": (
                    lead_counts.get(sector, 0) / available_counts.get(sector, np.nan)
                ),
            }
        )
    return pd.DataFrame(rows)


def _corridor_pressure(
    leads: pd.DataFrame, spots: pd.DataFrame, availability: pd.DataFrame
) -> pd.DataFrame:
    latest = (
        availability.sort_values(["spot_id", "snapshot_date"])
        .drop_duplicates("spot_id", keep="last")
        .merge(spots[["spot_id", "corridor"]], on="spot_id", how="left")
    )
    lead_counts = leads["preferred_corridor"].fillna("<MISSING>").value_counts()
    spot_counts = spots["corridor"].fillna("<MISSING>").value_counts()
    available_counts = (
        latest.loc[latest["is_available"], "corridor"].fillna("<MISSING>").value_counts()
    )
    rows = []
    for corridor in sorted(set(lead_counts.index) | set(spot_counts.index)):
        available = int(available_counts.get(corridor, 0))
        rows.append(
            {
                "corridor": corridor,
                "leads": int(lead_counts.get(corridor, 0)),
                "spots": int(spot_counts.get(corridor, 0)),
                "latest_available_spots": available,
                "leads_per_available_spot": (
                    lead_counts.get(corridor, 0) / available if available > 0 else np.nan
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("leads", ascending=False)


def _market_sector_summary(market: pd.DataFrame) -> pd.DataFrame:
    return (
        market.groupby("sector")
        .agg(
            rows=("sector", "size"),
            median_avg_price_sqm_mxn=("avg_price_sqm_mxn", "median"),
            mean_recent_occupancy_rate=("recent_occupancy_rate", "mean"),
            median_absorption_velocity_days=("absorption_velocity_days", "median"),
            median_recent_inquiry_volume=("recent_inquiry_volume", "median"),
            median_similar_available_spots=("similar_available_spots", "median"),
        )
        .reset_index()
    )


def _response_time_table(inquiries: pd.DataFrame) -> pd.DataFrame:
    d = inquiries[inquiries["broker_response_hours"].notna()].copy()
    d["response_bucket"] = pd.cut(
        d["broker_response_hours"],
        bins=[-np.inf, 2, 6, 12, 24, 48, np.inf],
        labels=["<=2h", "2-6h", "6-12h", "12-24h", "24-48h", ">48h"],
        right=True,
    )
    d["scheduled_visit"] = d["broker_response"].eq("scheduled_visit").astype(int)
    return (
        d.groupby("response_bucket", observed=True)["scheduled_visit"]
        .agg(["size", "mean"])
        .reset_index()
        .rename(columns={"size": "n", "mean": "scheduled_visit_rate"})
    )


def _temporal_proxy(t0: pd.DataFrame) -> pd.DataFrame:
    d = t0.copy()
    d["lead_month"] = d["created_at"].dt.to_period("M").astype(str)
    return (
        d.groupby("lead_month")["target_30d"]
        .agg(["size", "mean"])
        .reset_index()
        .rename(columns={"size": "n", "mean": "proxy_positive_rate"})
    )


def _current_state_diagnostic(spots: pd.DataFrame, inquiries: pd.DataFrame) -> dict[str, float]:
    observed = inquiries.groupby("spot_id").size().rename("observed_inquiries")
    d = spots[["spot_id", "total_inquiries"]].merge(
        observed, left_on="spot_id", right_index=True, how="left"
    )
    d["observed_inquiries"] = d["observed_inquiries"].fillna(0)
    d["difference"] = d["total_inquiries"] - d["observed_inquiries"]
    return {
        "exact_match_rate": float(d["difference"].eq(0).mean()),
        "difference_median": float(d["difference"].median()),
        "difference_p05": float(d["difference"].quantile(0.05)),
        "difference_p95": float(d["difference"].quantile(0.95)),
        "difference_min": float(d["difference"].min()),
        "difference_max": float(d["difference"].max()),
    }


def _attribute_sentinel_table(
    attrs: pd.DataFrame, spots: pd.DataFrame
) -> pd.DataFrame:
    d = attrs.merge(spots[["spot_id", "sector_name"]], on="spot_id", how="left")
    rows = []
    for column in ["vertical_height_m", "elevators", "parking_spaces"]:
        grouped = d.groupby("sector_name")[column].agg(
            n="size", zero_rate=lambda x: float(x.eq(0).mean()), missing_rate=lambda x: float(x.isna().mean())
        )
        for sector, row in grouped.iterrows():
            rows.append(
                {
                    "column": column,
                    "sector": sector,
                    "n": int(row["n"]),
                    "zero_rate": float(row["zero_rate"]),
                    "missing_rate": float(row["missing_rate"]),
                }
            )
    return pd.DataFrame(rows)



def _raw_distribution_summary(
    leads: pd.DataFrame, spots: pd.DataFrame
) -> pd.DataFrame:
    sectors = sorted(set(leads["search_sector"].dropna()) | set(spots["sector_name"].dropna()))
    rows = []
    for sector in sectors:
        lead_slice = leads[leads["search_sector"].eq(sector)]
        spot_slice = spots[spots["sector_name"].eq(sector)]
        rows.append(
            {
                "sector": sector,
                "leads": len(lead_slice),
                "spots": len(spot_slice),
                "lead_target_area_median": lead_slice["target_area_sqm"].median(),
                "spot_area_median": spot_slice["area_sqm"].median(),
                "lead_max_rent_budget_median": lead_slice["max_budget_mxn_rent_monthly"].median(),
                "spot_total_rent_median": spot_slice["price_total_mxn_rent"].median(),
                "lead_max_sale_budget_median": lead_slice["max_budget_mxn_sale_total"].median(),
                "spot_total_sale_median": spot_slice["price_total_mxn_sale"].median(),
            }
        )
    return pd.DataFrame(rows)


def _stage_information_audit() -> pd.DataFrame:
    rows = [
        {
            "information_family": "Lead profile",
            "examples": "user_type, company_size, industry, search_sector, search_modality, budgets, preferred geography, source",
            "T0_lead_creation": "ALLOW",
            "T1_first_inquiry": "ALLOW",
            "T2_second_inquiry": "ALLOW",
            "eda_interpretation": "Observed at lead creation; descriptive distributions are valid from T0 onward.",
        },
        {
            "information_family": "First-inquiry content",
            "examples": "channel, message_length, requested_area, requested_budget, urgency_days, asked_visit",
            "T0_lead_creation": "BLOCK",
            "T1_first_inquiry": "ALLOW",
            "T2_second_inquiry": "ALLOW",
            "eda_interpretation": "Becomes observable only when the first inquiry arrives.",
        },
        {
            "information_family": "Current inquiry content",
            "examples": "channel, requested_area, requested_budget, urgency_days, asked_visit at the scoring inquiry",
            "T0_lead_creation": "BLOCK",
            "T1_first_inquiry": "ALLOW",
            "T2_second_inquiry": "ALLOW",
            "eda_interpretation": "At each inquiry head, current and prior inquiry content is observable at scoring time.",
        },
        {
            "information_family": "Broker response to current inquiry",
            "examples": "broker_response, broker_response_hours",
            "T0_lead_creation": "BLOCK",
            "T1_first_inquiry": "BLOCK",
            "T2_second_inquiry": "BLOCK",
            "eda_interpretation": "Post-inquiry information; cannot be used by a head scored at the inquiry timestamp.",
        },
        {
            "information_family": "Prior broker responses",
            "examples": "responses to inquiries before current scoring time",
            "T0_lead_creation": "BLOCK",
            "T1_first_inquiry": "BLOCK",
            "T2_second_inquiry": "CONDITIONAL",
            "eda_interpretation": "Eligible at later heads only when response timing proves the event precedes scoring.",
        },
        {
            "information_family": "Inquiry spot static identity",
            "examples": "spot_id, sector_name, modality, geography, base listing attributes",
            "T0_lead_creation": "NOT_APPLICABLE",
            "T1_first_inquiry": "ALLOW",
            "T2_second_inquiry": "ALLOW",
            "eda_interpretation": "The contacted spot becomes known at inquiry time; mutable listing fields need separate historical validation.",
        },
        {
            "information_family": "Spot current-state aggregates",
            "examples": "days_on_market, total_inquiries, total_views, is_active",
            "T0_lead_creation": "BLOCK",
            "T1_first_inquiry": "BLOCK",
            "T2_second_inquiry": "BLOCK",
            "eda_interpretation": "Unsafe for historical scoring unless reconstructed point in time.",
        },
        {
            "information_family": "Availability snapshot",
            "examples": "latest snapshot with snapshot_date <= scoring time",
            "T0_lead_creation": "CONDITIONAL",
            "T1_first_inquiry": "CONDITIONAL",
            "T2_second_inquiry": "CONDITIONAL",
            "eda_interpretation": "Valid only with a non-future snapshot-selection rule.",
        },
        {
            "information_family": "Market context",
            "examples": "state x municipality x corridor x sector x month",
            "T0_lead_creation": "CONDITIONAL",
            "T1_first_inquiry": "CONDITIONAL",
            "T2_second_inquiry": "CONDITIONAL",
            "eda_interpretation": "A monthly row is not automatically known before every scoring date.",
        },
        {
            "information_family": "Broker identity",
            "examples": "spots.broker_id for the contacted spot",
            "T0_lead_creation": "NOT_APPLICABLE",
            "T1_first_inquiry": "ALLOW",
            "T2_second_inquiry": "ALLOW",
            "eda_interpretation": "Observable through the contacted spot; no broker master table is supplied.",
        },
        {
            "information_family": "Broker historical profile",
            "examples": "prior inquiry/response history for broker",
            "T0_lead_creation": "NOT_APPLICABLE",
            "T1_first_inquiry": "CONDITIONAL",
            "T2_second_inquiry": "CONDITIONAL",
            "eda_interpretation": "Must use only events available strictly before scoring.",
        },
        {
            "information_family": "Outcome proxy",
            "examples": "scheduled_visit in the next 30 days",
            "T0_lead_creation": "LABEL_ONLY",
            "T1_first_inquiry": "LABEL_ONLY",
            "T2_second_inquiry": "LABEL_ONLY",
            "eda_interpretation": "Future events may define y but must never appear in X.",
        },
    ]
    return pd.DataFrame(rows)



def _numeric_summary(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table, frame in data.items():
        numeric = frame.select_dtypes(include=[np.number, "bool"]).columns
        for column in numeric:
            series = pd.to_numeric(frame[column], errors="coerce")
            valid = series.dropna()
            rows.append(
                {
                    "table": table,
                    "column": column,
                    "n": int(valid.size),
                    "missing_rate": float(series.isna().mean()),
                    "mean": valid.mean(),
                    "std": valid.std(),
                    "min": valid.min(),
                    "p01": valid.quantile(0.01),
                    "p05": valid.quantile(0.05),
                    "p25": valid.quantile(0.25),
                    "median": valid.median(),
                    "p75": valid.quantile(0.75),
                    "p95": valid.quantile(0.95),
                    "p99": valid.quantile(0.99),
                    "max": valid.max(),
                }
            )
    return pd.DataFrame(rows)


def _categorical_summary(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table, frame in data.items():
        for column in frame.columns:
            series = frame[column]
            if pd.api.types.is_datetime64_any_dtype(series) or pd.api.types.is_numeric_dtype(series):
                continue
            values = series.dropna().astype(str)
            vc = values.value_counts()
            rows.append(
                {
                    "table": table,
                    "column": column,
                    "n_unique": int(values.nunique()),
                    "missing_rate": float(series.isna().mean()),
                    "top_value": vc.index[0] if len(vc) else None,
                    "top_count": int(vc.iloc[0]) if len(vc) else 0,
                    "top_share_nonmissing": float(vc.iloc[0] / len(values)) if len(values) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def _broker_summary(spots: pd.DataFrame, inquiries: pd.DataFrame) -> pd.DataFrame:
    spot_broker = spots[["spot_id", "broker_id"]].copy()
    spot_counts = spot_broker.groupby("broker_id").size().rename("spots")
    inquiry_broker = inquiries.merge(spot_broker, on="spot_id", how="left")
    inquiry_broker["scheduled_visit"] = inquiry_broker["broker_response"].eq("scheduled_visit").astype(int)
    inquiry_stats = inquiry_broker.groupby("broker_id").agg(
        inquiries=("inquiry_id", "size"),
        scheduled_visits=("scheduled_visit", "sum"),
        scheduled_visit_share=("scheduled_visit", "mean"),
    )
    return (
        spot_counts.to_frame()
        .join(inquiry_stats, how="outer")
        .fillna({"spots": 0, "inquiries": 0, "scheduled_visits": 0})
        .reset_index()
        .sort_values("inquiries", ascending=False)
    )


def make_figures(
    out_dir: Path,
    data: dict[str, pd.DataFrame],
    stage_summary: pd.DataFrame,
    stage_frames: dict[str, pd.DataFrame],
    t1_breakdowns: pd.DataFrame,
    availability_t1: pd.DataFrame,
    sector_balance: pd.DataFrame,
    corridor_pressure: pd.DataFrame,
    market_sector: pd.DataFrame,
    response_time: pd.DataFrame,
    missingness: pd.DataFrame,
) -> None:
    figures = out_dir / "figures"
    leads = data["leads"]

    for column, file_name, title in [
        ("search_sector", "01_lead_mix_sector.svg", "Lead mix by sector"),
        ("search_modality", "02_lead_mix_modality.svg", "Lead mix by modality"),
        ("user_type", "03_lead_mix_user_type.svg", "Lead mix by user type"),
    ]:
        counts = leads[column].fillna("<MISSING>").value_counts()
        _bar(
            counts.index.astype(str).tolist(),
            counts.values.astype(float).tolist(),
            figures / file_name,
            title,
            f"n={len(leads):,} leads",
        )

    sb = sector_balance.sort_values("sector")
    _grouped_bar(
        sb["sector"].tolist(),
        {
            "Lead share": sb["lead_share"].tolist(),
            "Latest available inventory share": sb["latest_available_share"].tolist(),
        },
        figures / "04_demand_vs_available_inventory_sector.svg",
        "Demand vs available inventory by sector",
        "Shares are normalized within leads and latest available spots; latest snapshot is descriptive, not a historical feature",
        percent=True,
    )

    _bar(
        stage_summary["stage"].tolist(),
        stage_summary["proxy_positive_rate"].tolist(),
        figures / "05_proxy_rate_by_head.svg",
        "30-day scheduled-visit proxy by candidate scoring head",
        "Rates use head-specific scoring anchors and right-censoring; not directly comparable as model metrics",
        percent=True,
    )

    temporal = _temporal_proxy(stage_frames["T0"])
    _line(
        temporal["lead_month"].tolist(),
        temporal["proxy_positive_rate"].tolist(),
        figures / "06_proxy_rate_by_lead_cohort_month.svg",
        "T0 proxy rate by lead cohort month",
        f"30-day proxy; final month is partial after right-censoring at {stage_frames['T0']['created_at'].max().date()}",
        percent=True,
    )

    lag = t1_breakdowns[t1_breakdowns["dimension"].eq("first_inquiry_lag_bucket")].copy()
    order = ["<1d", "1-3d", "3-7d", "7-30d", ">=30d"]
    lag["segment"] = pd.Categorical(lag["segment"], categories=order, ordered=True)
    lag = lag.sort_values("segment")
    _bar(
        lag["segment"].astype(str).tolist(),
        lag["proxy_positive_rate"].tolist(),
        figures / "07_first_inquiry_lag_vs_proxy.svg",
        "Time to first inquiry vs future scheduled-visit proxy",
        "T1 cohort only; raw association, not a causal effect",
        percent=True,
    )

    av = availability_t1.copy()
    av["segment"] = av["segment"].astype(str)
    av = av.sort_values("segment")
    _bar(
        av["segment"].tolist(),
        av["proxy_positive_rate"].tolist(),
        figures / "08_t1_availability_vs_proxy.svg",
        "As-of availability at first inquiry vs future proxy",
        "Uses latest snapshot on or before T1; missing snapshots excluded",
        percent=True,
    )

    _bar(
        response_time["response_bucket"].astype(str).tolist(),
        response_time["scheduled_visit_rate"].tolist(),
        figures / "09_response_time_vs_scheduled_visit.svg",
        "Broker response time vs scheduled-visit share",
        "Descriptive only; broker response is post-inquiry information and must not be used at T1",
        percent=True,
    )

    _bar(
        stage_summary["stage"].tolist(),
        stage_summary["eligible_rows"].astype(float).tolist(),
        figures / "10_stage_coverage.svg",
        "Eligible sample size by candidate head",
        "30-day right-censoring applied; T2/T3 also exclude prior scheduled visits",
    )

    ms = market_sector.sort_values("sector")
    _bar(
        ms["sector"].tolist(),
        ms["mean_recent_occupancy_rate"].tolist(),
        figures / "11_market_occupancy_by_sector.svg",
        "Recent occupancy rate by sector",
        "Mean across available market-context rows; monthly context is not automatically point-in-time safe",
        percent=True,
    )
    _bar(
        ms["sector"].tolist(),
        ms["median_absorption_velocity_days"].tolist(),
        figures / "12_market_absorption_by_sector.svg",
        "Absorption velocity by sector",
        "Median days across market-context rows; lower is faster",
    )

    cp = corridor_pressure[
        corridor_pressure["corridor"].ne("<MISSING>")
        & corridor_pressure["latest_available_spots"].gt(0)
    ].nlargest(10, "leads_per_available_spot")
    _bar(
        cp["corridor"].tolist(),
        cp["leads_per_available_spot"].tolist(),
        figures / "13_corridor_pressure.svg",
        "Highest current demand pressure by corridor",
        "Leads per latest available spot; descriptive current-state ratio, not a historical feature",
        horizontal=True,
    )

    miss = missingness[missingness["missing_rate"].gt(0)].nlargest(12, "missing_rate").copy()
    miss["label"] = miss["table"] + "." + miss["column"]
    _bar(
        miss["label"].tolist(),
        miss["missing_rate"].tolist(),
        figures / "14_missingness_top.svg",
        "Largest missingness rates",
        "Several price/budget nulls are structural by modality; see tables/missingness.csv",
        percent=True,
        horizontal=True,
    )


def build_eda(repo_root: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = out_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    data = load_data(repo_root)
    profile = _profile_table(data)
    missingness = _missingness_table(data)
    stage_summary, stage_frames, censor_cutoff = build_stage_table(
        data["leads"], data["inquiries"]
    )

    segment_rates = pd.concat(
        [
            _segment_rates(
                stage_frames[stage],
                ["search_sector", "search_modality", "user_type", "source", "company_size"],
                stage,
            )
            for stage in stage_frames
            if not stage_frames[stage].empty
        ],
        ignore_index=True,
    )
    t1_breakdowns = _t1_breakdowns(stage_frames["T1"])
    join_quality = _join_quality(data)
    availability_asof, availability_t1 = _availability_asof_t1(
        stage_frames["T1"], data["availability_snapshot"]
    )
    sector_balance = _sector_balance(
        data["leads"], data["spots"], data["availability_snapshot"]
    )
    corridor_pressure = _corridor_pressure(
        data["leads"], data["spots"], data["availability_snapshot"]
    )
    market_sector = _market_sector_summary(data["market_context"])
    response_time = _response_time_table(data["inquiries"])
    sentinel = _attribute_sentinel_table(data["spot_attributes"], data["spots"])
    temporal_proxy = _temporal_proxy(stage_frames["T0"])
    raw_distribution = _raw_distribution_summary(data["leads"], data["spots"])
    stage_information_audit = _stage_information_audit()
    numeric_summary = _numeric_summary(data)
    categorical_summary = _categorical_summary(data)
    broker_summary = _broker_summary(data["spots"], data["inquiries"])

    availability_coverage = float(availability_asof["snapshot_id"].notna().mean())
    latest_availability = (
        data["availability_snapshot"]
        .sort_values(["spot_id", "snapshot_date"])
        .drop_duplicates("spot_id", keep="last")
    )

    summary = {
        "analysis_scope": "EDA only; no feature engineering and no model fitting",
        "target_proxy": {
            "event": "broker_response == scheduled_visit",
            "horizon_days": HORIZON_DAYS,
            "timestamp_caveat": "scheduled_visit is recorded on an inquiry row; the exact visit-scheduling timestamp is not present",
            "censor_cutoff": censor_cutoff,
        },
        "datasets": {
            name: {"rows": len(df), "columns": len(df.columns)}
            for name, df in data.items()
        },
        "stage_summary": stage_summary.to_dict(orient="records"),
        "t1_asof_availability_coverage": availability_coverage,
        "latest_availability_rate": float(latest_availability["is_available"].mean()),
        "market_context_exact_t0_coverage": float(
            join_quality.loc[
                join_quality["check"].eq("exact lead-market context coverage at lead month"),
                "value",
            ].iloc[0]
        ),
        "current_state_total_inquiries_diagnostic": _current_state_diagnostic(
            data["spots"], data["inquiries"]
        ),
        "key_observations": {
            "first_inquiry_lag": t1_breakdowns[
                t1_breakdowns["dimension"].eq("first_inquiry_lag_bucket")
            ].to_dict(orient="records"),
            "response_time": response_time.to_dict(orient="records"),
            "availability_at_t1": availability_t1.to_dict(orient="records"),
            "sector_balance": sector_balance.to_dict(orient="records"),
        },
    }

    profile.to_csv(tables_dir / "dataset_profile.csv", index=False)
    missingness.to_csv(tables_dir / "missingness.csv", index=False)
    stage_summary.to_csv(tables_dir / "stage_summary.csv", index=False)
    segment_rates.to_csv(tables_dir / "proxy_rates_by_segment.csv", index=False)
    t1_breakdowns.to_csv(tables_dir / "t1_breakdowns.csv", index=False)
    join_quality.to_csv(tables_dir / "join_quality.csv", index=False)
    availability_t1.to_csv(tables_dir / "availability_at_t1.csv", index=False)
    sector_balance.to_csv(tables_dir / "sector_balance.csv", index=False)
    corridor_pressure.to_csv(tables_dir / "corridor_pressure.csv", index=False)
    market_sector.to_csv(tables_dir / "market_sector_summary.csv", index=False)
    response_time.to_csv(tables_dir / "response_time_diagnostic.csv", index=False)
    sentinel.to_csv(tables_dir / "attribute_sentinel_diagnostic.csv", index=False)
    temporal_proxy.to_csv(tables_dir / "proxy_by_lead_month.csv", index=False)
    raw_distribution.to_csv(tables_dir / "raw_distribution_summary.csv", index=False)
    stage_information_audit.to_csv(tables_dir / "stage_information_audit.csv", index=False)
    numeric_summary.to_csv(tables_dir / "numeric_summary.csv", index=False)
    categorical_summary.to_csv(tables_dir / "categorical_summary.csv", index=False)
    broker_summary.to_csv(tables_dir / "broker_summary.csv", index=False)

    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(_jsonable(summary), f, indent=2, ensure_ascii=False)

    make_figures(
        out_dir,
        data,
        stage_summary,
        stage_frames,
        t1_breakdowns,
        availability_t1,
        sector_balance,
        corridor_pressure,
        market_sector,
        response_time,
        missingness,
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Spot2 EDA for the multi-head modeling design.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument(
        "--out-dir",
        default="experimentos/eda_profundo/base_eda",
        help="Output directory. Keep it under experimentos/eda_profundo/base_eda for this project.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = (repo_root / args.out_dir).resolve()
    summary = build_eda(repo_root, out_dir)
    print(json.dumps(_jsonable(summary), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
