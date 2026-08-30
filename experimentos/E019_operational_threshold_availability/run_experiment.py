from __future__ import annotations

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

OOF = ROOT / "experimentos/modelo_3/trajectory_cv/results/oof_predictions.csv"
DATA = ROOT / "data/candidate/csv"
MODEL_COL = "pooled_catboost_trajectory"
CAPACITIES = [0.05, 0.10, 0.15, 0.20, 0.30]
HORIZON = pd.Timedelta(days=30)


def capacity_metrics(df: pd.DataFrame, capacity: float) -> dict:
    d = df.sort_values(MODEL_COL, ascending=False).reset_index(drop=True)
    n_sel = max(1, math.ceil(len(d) * capacity))
    top = d.iloc[:n_sel]
    base_rate = d["target_30d"].mean()
    top_rate = top["target_30d"].mean()
    positives = d["target_30d"].sum()
    return {
        "selected": n_sel,
        "threshold": float(top[MODEL_COL].iloc[-1]),
        "top_rate": float(top_rate),
        "lift": float(top_rate / base_rate),
        "recall": float(top["target_30d"].sum() / positives),
    }


def build_threshold_frontier() -> pd.DataFrame:
    oof = pd.read_csv(OOF)
    rows = []
    for stage in ["T0_cold", "T1_first_inquiry", "T2_engaged"]:
        for capacity in CAPACITIES:
            per_fold = []
            for fold, g in oof[oof["stage"].eq(stage)].groupby("fold"):
                m = capacity_metrics(g, capacity)
                per_fold.append({"fold": fold, **m})
            z = pd.DataFrame(per_fold)
            rows.append(
                {
                    "stage": stage,
                    "capacity": capacity,
                    "mean_lift": z["lift"].mean(),
                    "mean_recall": z["recall"].mean(),
                    "mean_top_rate": z["top_rate"].mean(),
                    "median_raw_threshold": z["threshold"].median(),
                    "min_raw_threshold": z["threshold"].min(),
                    "max_raw_threshold": z["threshold"].max(),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "threshold_frontier.csv", index=False)
    return out


def latest_asof_index(times: np.ndarray, t: np.datetime64) -> int:
    return int(np.searchsorted(times, t, side="right") - 1)


def build_availability_events() -> pd.DataFrame:
    iq = pd.read_csv(DATA / "inquiries.csv", parse_dates=["inquiry_at"])
    spots = pd.read_csv(DATA / "spots.csv", usecols=["spot_id", "sector_name"])
    av = pd.read_csv(DATA / "availability_snapshot.csv", parse_dates=["snapshot_date"])
    av["is_available"] = av["is_available"].astype(str).str.lower().eq("true")
    av = av.sort_values(["spot_id", "snapshot_date"])

    sector = spots.set_index("spot_id")["sector_name"].to_dict()
    by_spot = {
        int(sid): g[["snapshot_date", "is_available"]].reset_index(drop=True)
        for sid, g in av.groupby("spot_id", sort=False)
    }

    rows = []
    for r in iq.itertuples(index=False):
        g = by_spot.get(int(r.spot_id))
        if g is None:
            continue

        times = g["snapshot_date"].values.astype("datetime64[ns]")
        t = np.datetime64(r.inquiry_at.to_datetime64())
        j = latest_asof_index(times, t)
        if j < 0:
            continue

        current_available = bool(g.loc[j, "is_available"])
        if current_available:
            y = 1
            label_mature_at = r.inquiry_at
        else:
            end = r.inquiry_at + HORIZON
            future = g[
                (g["snapshot_date"] > r.inquiry_at)
                & (g["snapshot_date"] <= end)
            ]
            if future.empty:
                continue
            y = int(future["is_available"].any())
            label_mature_at = end

        rows.append(
            {
                "inquiry_at": r.inquiry_at,
                "label_mature_at": label_mature_at,
                "spot_id": int(r.spot_id),
                "sector_name": sector.get(int(r.spot_id), "UNKNOWN"),
                "current_available": int(current_available),
                "availability_30d": y,
            }
        )

    return pd.DataFrame(rows).sort_values("inquiry_at").reset_index(drop=True)


def availability_probability_cv(events: pd.DataFrame) -> pd.DataFrame:
    unique_times = np.sort(events["inquiry_at"].unique())
    cuts = [
        unique_times[int((len(unique_times) - 1) * q)]
        for q in [0.20, 0.40, 0.60, 0.80, 1.00]
    ]

    rows = []
    start = pd.Timestamp(cuts[0])
    sectors = ["Office", "Industrial", "Retail", "Land"]

    for fold in range(1, 5):
        end = pd.Timestamp(cuts[fold])
        train = events[events["label_mature_at"] < start].copy()
        test = events[
            (events["inquiry_at"] >= start) & (events["inquiry_at"] <= end)
        ].copy()

        unavailable = train[train["current_available"].eq(0)]
        global_p = float(unavailable["availability_30d"].mean())

        sector_p = {}
        for sector in sectors:
            g = unavailable[unavailable["sector_name"].eq(sector)]
            n = len(g)
            sector_p[sector] = (
                float((g["availability_30d"].sum() + 20 * global_p) / (n + 20))
                if n
                else global_p
            )

        test["p_availability_30d"] = np.where(
            test["current_available"].eq(1),
            1.0,
            test["sector_name"].map(sector_p).fillna(global_p),
        )

        y = test["availability_30d"].astype(int)
        p = test["p_availability_30d"].astype(float)
        rows.append(
            {
                "fold": fold,
                "train_n": len(train),
                "test_start": start.date().isoformat(),
                "test_end": end.date().isoformat(),
                "global_unavail_p": global_p,
                **sector_p,
                "n": len(test),
                "positive_rate": float(y.mean()),
                "auc": float(roc_auc_score(y, p)),
                "brier": float(brier_score_loss(y, p)),
                "log_loss": float(log_loss(y, p, labels=[0, 1])),
            }
        )
        start = end

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "availability_cv_metrics.csv", index=False)
    return out


def lead_availability_probability(candidate_spot_probabilities: pd.Series) -> float:
    """Conservative serviceability aggregation for an already compatible pool."""
    if candidate_spot_probabilities.empty:
        return 0.0
    return float(candidate_spot_probabilities.max())


def main() -> None:
    threshold = build_threshold_frontier()
    events = build_availability_events()
    av_cv = availability_probability_cv(events)

    summary = {
        "threshold_policy": {
            "T0_cold": "no_priority_gate",
            "T1_first_inquiry": "top_15pct_within_stage",
            "T2_engaged": "top_15pct_within_stage",
            "raw_threshold_policy": "diagnostic_only_not_frozen",
        },
        "availability": {
            "observable_events": int(len(events)),
            "macro_auc": float(av_cv["auc"].mean()),
            "macro_brier": float(av_cv["brier"].mean()),
            "macro_log_loss": float(av_cv["log_loss"].mean()),
            "lead_aggregation": "max candidate p_availability_30d over compatible pool",
        },
        "artifacts": {
            "threshold_frontier": "results/threshold_frontier.csv",
            "availability_cv_metrics": "results/availability_cv_metrics.csv",
        },
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(threshold.to_string(index=False))
    print(av_cv.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
