"""Compact, reproducible EDA used by the notebook and executive deliverables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .contracts import Settings


def _save(fig: plt.Figure, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def build_eda(tables: dict[str, pd.DataFrame], t1: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    figures = settings.codexway_root / "outputs" / "figures"
    output_tables = settings.codexway_root / "outputs" / "tables"
    metrics = settings.codexway_root / "outputs" / "metrics"
    figures.mkdir(parents=True, exist_ok=True); output_tables.mkdir(parents=True, exist_ok=True)
    leads, inquiries, market = tables["leads"].copy(), tables["inquiries"].copy(), tables["market_context"].copy()

    # Business mix and demand volume.
    mix = leads.groupby(["search_sector", "search_modality"], dropna=False).size().rename("leads").reset_index()
    mix["share"] = mix["leads"] / len(leads)
    mix.to_csv(output_tables / "lead_mix.csv", index=False)
    pivot = mix.pivot(index="search_sector", columns="search_modality", values="leads").fillna(0)
    fig, ax = plt.subplots(figsize=(9, 4.8)); pivot.plot.bar(stacked=True, ax=ax, color=["#6C63FF", "#00A6A6", "#FFB703"][:len(pivot.columns)])
    ax.set(title="Lead demand mix", xlabel="Sector", ylabel="Leads"); ax.legend(title="Modality")
    lead_mix_path = _save(fig, figures / "eda_lead_mix.png")

    lead_month = leads.assign(month=leads["created_at"].dt.strftime("%Y-%m")).groupby("month").size().rename("leads")
    inquiry_month = inquiries.assign(month=inquiries["inquiry_at"].dt.strftime("%Y-%m")).groupby("month").size().rename("inquiries")
    volume = pd.concat([lead_month, inquiry_month], axis=1).fillna(0).reset_index()
    volume.to_csv(output_tables / "monthly_volume.csv", index=False)
    fig, ax1 = plt.subplots(figsize=(10, 4.7)); ax2 = ax1.twinx()
    ax1.plot(volume["month"], volume["leads"], marker="o", color="#6C63FF", label="Leads")
    ax2.plot(volume["month"], volume["inquiries"], marker="o", color="#00A6A6", label="Inquiries")
    ax1.set(title="Demand volume over time", xlabel="Month", ylabel="Leads"); ax2.set_ylabel("Inquiries")
    ax1.tick_params(axis="x", rotation=45)
    volume_path = _save(fig, figures / "eda_monthly_volume.png")

    mature = t1[t1["target_t1"].notna()].copy()
    segment_rows = []
    for column in ["search_sector", "search_modality", "user_type", "source", "channel"]:
        group = mature.groupby(column, dropna=False)["target_t1"].agg(["size", "mean"]).reset_index()
        group.columns = ["value", "n", "positive_rate"]
        group.insert(0, "segment", column); segment_rows.append(group)
    segments = pd.concat(segment_rows, ignore_index=True)
    segments.to_csv(output_tables / "target_rate_by_segment.csv", index=False)
    shown = segments[(segments["segment"].isin(["search_sector", "source"])) & segments["n"].ge(50)].copy()
    shown["label"] = shown["segment"] + ": " + shown["value"].astype(str)
    shown = shown.sort_values("positive_rate")
    fig, ax = plt.subplots(figsize=(9, 5)); ax.barh(shown["label"], shown["positive_rate"], color="#6C63FF")
    ax.axvline(mature["target_t1"].mean(), color="#D62828", linestyle="--", label="Global")
    ax.set(title="First-inquiry outcome by major segment", xlabel="Scheduled-visit rate"); ax.legend()
    segment_path = _save(fig, figures / "eda_target_segments.png")

    # Market is contextual EDA only: month is not a reliable effective/publication timestamp.
    market_summary = market.groupby("sector", dropna=False).agg(
        rows=("month", "size"), months=("month", "nunique"),
        median_available_spots=("similar_available_spots", "median"),
        median_price_sqm_mxn=("avg_price_sqm_mxn", "median"),
        median_occupancy=("recent_occupancy_rate", "median"),
        median_absorption_days=("absorption_velocity_days", "median"),
        median_inquiry_volume=("recent_inquiry_volume", "median"),
    ).reset_index()
    market_summary["model_use"] = "EDA_ONLY__PUBLICATION_TIME_UNKNOWN"
    market_summary.to_csv(output_tables / "market_context_eda.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].bar(market_summary["sector"].astype(str), market_summary["median_price_sqm_mxn"], color="#00A6A6")
    axes[0].set(title="Market asking price context", ylabel="Median MXN / sqm"); axes[0].tick_params(axis="x", rotation=30)
    axes[1].bar(market_summary["sector"].astype(str), market_summary["median_absorption_days"], color="#FFB703")
    axes[1].set(title="Market absorption context", ylabel="Median days"); axes[1].tick_params(axis="x", rotation=30)
    market_path = _save(fig, figures / "eda_market_context.png")

    quality_rows = []
    for table_name, frame in tables.items():
        for column in frame.columns:
            missing = float(frame[column].isna().mean())
            if missing > 0:
                quality_rows.append({"table": table_name, "column": column, "missing_share": missing, "rows": len(frame)})
    quality = pd.DataFrame(quality_rows).sort_values("missing_share", ascending=False)
    quality.to_csv(output_tables / "data_quality_missingness.csv", index=False)

    summary = {
        "status": "COMPLETE",
        "lead_rows": int(len(leads)), "inquiry_rows": int(len(inquiries)),
        "mature_t1_rows": int(len(mature)), "t1_positive_rate": float(mature["target_t1"].mean()),
        "largest_lead_mix": mix.sort_values("share", ascending=False).head(5).to_dict(orient="records"),
        "market_context_status": "EDA_ONLY__NOT_A_MODEL_FEATURE",
        "market_rows": int(len(market)), "market_strata": int(market[["state", "municipality", "corridor", "sector"]].drop_duplicates().shape[0]),
        "figures": [str(path) for path in [lead_mix_path, volume_path, segment_path, market_path]],
    }
    (metrics / "eda_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
