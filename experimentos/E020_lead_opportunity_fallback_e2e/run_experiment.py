from __future__ import annotations

import json
import math
from bisect import bisect_right
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "data/candidate/csv"
OOF = ROOT / "experimentos/modelo_3/trajectory_cv/results/oof_predictions.csv"
E019_AV = ROOT / "experimentos/E019_operational_threshold_availability/results/availability_cv_metrics.csv"
OUT = HERE / "results"
OUT.mkdir(parents=True, exist_ok=True)

QUALITY_COL = "pooled_catboost_trajectory"
K_FINAL = 3
CAPACITY = 0.15
AREA_MIN = 0.50
AREA_MAX = 2.00
BUDGET_MAX_RATIO = 1.50


def as_bool(x: object) -> bool:
    return str(x).strip().lower() in {"true", "1", "yes"}


def load_inputs():
    leads = pd.read_csv(DATA / "leads.csv")
    spots = pd.read_csv(DATA / "spots.csv", parse_dates=["created_at"])
    iq = pd.read_csv(DATA / "inquiries.csv", parse_dates=["inquiry_at"])
    av = pd.read_csv(DATA / "availability_snapshot.csv", parse_dates=["snapshot_date"])
    oof = pd.read_csv(OOF, parse_dates=["score_time"])
    av_rates = pd.read_csv(E019_AV)

    hours = pd.to_numeric(iq["broker_response_hours"], errors="coerce")
    iq["response_event_at"] = iq["inquiry_at"] + pd.to_timedelta(hours, unit="h")
    iq.loc[hours.isna(), "response_event_at"] = pd.NaT
    av["is_available_bool"] = av["is_available"].map(as_bool)

    return leads, spots, iq, av, oof, av_rates


def build_availability_index(av: pd.DataFrame):
    idx = {}
    for spot_id, g in av.sort_values(["spot_id", "snapshot_date"]).groupby("spot_id"):
        times = g["snapshot_date"].tolist()
        vals = list(zip(g["is_available_bool"].astype(bool), g["days_until_available"]))
        idx[int(spot_id)] = (times, vals)
    return idx


def latest_snapshot(index, spot_id: int, score_time: pd.Timestamp):
    item = index.get(int(spot_id))
    if item is None:
        return None
    times, vals = item
    pos = bisect_right(times, score_time) - 1
    if pos < 0:
        return None
    available, days_until = vals[pos]
    return {
        "snapshot_date": times[pos],
        "is_available": bool(available),
        "days_until_available": days_until,
    }


def build_rate_maps(av_rates: pd.DataFrame):
    sectors = ["Office", "Industrial", "Retail", "Land"]
    sector_p = {}
    global_p = {}
    for r in av_rates.itertuples(index=False):
        f = int(r.fold)
        global_p[f] = float(r.global_unavail_p)
        sector_p[f] = {s: float(getattr(r, s)) for s in sectors}
    return sector_p, global_p


def modality_ok(lead_modality: str, spot_modality: str) -> bool:
    return (
        lead_modality == "both"
        or spot_modality == "both"
        or lead_modality == spot_modality
    )


def geo_tier(lead: pd.Series, spot) -> int:
    if pd.notna(lead["preferred_corridor"]) and spot.corridor == lead["preferred_corridor"]:
        return 0
    if pd.notna(lead["preferred_municipality"]) and spot.municipality == lead["preferred_municipality"]:
        return 1
    if pd.notna(lead["preferred_state"]) and spot.state == lead["preferred_state"]:
        return 2
    return 3


def relevant_price(lead: pd.Series, current: pd.Series, spot):
    options = []

    rent_budget = current["requested_budget_mxn_rent_monthly"]
    if pd.isna(rent_budget):
        rent_budget = lead["max_budget_mxn_rent_monthly"]

    sale_budget = current["requested_budget_mxn_sale_total"]
    if pd.isna(sale_budget):
        sale_budget = lead["max_budget_mxn_sale_total"]

    if (
        lead["search_modality"] in {"rent", "both"}
        and spot.modality in {"rent", "both"}
        and pd.notna(rent_budget)
        and pd.notna(spot.price_total_mxn_rent)
        and pd.notna(spot.price_sqm_mxn_rent)
    ):
        options.append(
            {
                "mode": "rent",
                "budget": float(rent_budget),
                "total": float(spot.price_total_mxn_rent),
                "price_sqm": float(spot.price_sqm_mxn_rent),
            }
        )

    if (
        lead["search_modality"] in {"sale", "both"}
        and spot.modality in {"sale", "both"}
        and pd.notna(sale_budget)
        and pd.notna(spot.price_total_mxn_sale)
        and pd.notna(spot.price_sqm_mxn_sale)
    ):
        options.append(
            {
                "mode": "sale",
                "budget": float(sale_budget),
                "total": float(spot.price_total_mxn_sale),
                "price_sqm": float(spot.price_sqm_mxn_sale),
            }
        )

    if not options:
        return None

    # For search_modality=both, choose the feasible economic basis that consumes
    # the smaller share of its corresponding max budget.
    options.sort(key=lambda x: x["total"] / x["budget"])
    return options[0]


def p_spot_available(
    spot_id: int,
    score_time: pd.Timestamp,
    fold: int,
    spot_lookup: dict,
    av_index: dict,
    sector_p: dict,
    global_p: dict,
) -> float:
    spot = spot_lookup[int(spot_id)]
    snap = latest_snapshot(av_index, int(spot_id), score_time)
    if snap is not None and snap["is_available"]:
        return 1.0
    return float(sector_p[fold].get(spot.sector_name, global_p[fold]))


def rank_fallback(
    lead: pd.Series,
    current: pd.Series,
    score_time: pd.Timestamp,
    fold: int,
    spots_by_sector: dict,
    spot_lookup: dict,
    av_index: dict,
    sector_p: dict,
    global_p: dict,
):
    req_area = current["requested_area_sqm"]
    if pd.isna(req_area):
        req_area = lead["target_area_sqm"]
    if pd.isna(req_area) or float(req_area) <= 0:
        return []

    req_area = float(req_area)
    current_spot_id = int(current["spot_id"])
    rows = []

    for spot in spots_by_sector.get(lead["search_sector"], []):
        if int(spot.spot_id) == current_spot_id:
            continue
        if pd.Timestamp(spot.created_at) > score_time:
            continue
        if not modality_ok(lead["search_modality"], spot.modality):
            continue

        snap = latest_snapshot(av_index, int(spot.spot_id), score_time)
        if snap is None:
            # Recommendation output requires an observed inventory state.
            continue

        tier = geo_tier(lead, spot)
        if tier > 2:
            continue

        if pd.isna(spot.area_sqm) or float(spot.area_sqm) <= 0:
            continue
        area_ratio = float(spot.area_sqm) / req_area
        if area_ratio < AREA_MIN or area_ratio > AREA_MAX:
            continue

        price = relevant_price(lead, current, spot)
        if price is None:
            continue
        budget_ratio = price["total"] / price["budget"]
        if budget_ratio > BUDGET_MAX_RATIO:
            continue

        target_price_sqm = price["budget"] / req_area
        area_dist = abs(math.log(area_ratio))
        price_dist = abs(
            math.log(max(price["price_sqm"], 1.0) / max(target_price_sqm, 1.0))
        )

        p_av = p_spot_available(
            int(spot.spot_id),
            score_time,
            fold,
            spot_lookup,
            av_index,
            sector_p,
            global_p,
        )

        rows.append(
            {
                "spot_id": int(spot.spot_id),
                "geo_tier": tier,
                "is_available_now": bool(snap["is_available"]),
                "p_availability": p_av,
                "fit_distance": area_dist + price_dist,
                "strict": bool(
                    tier == 0
                    and 0.50 <= area_ratio <= 1.50
                    and budget_ratio <= 1.15
                ),
            }
        )

    rows.sort(
        key=lambda x: (
            x["geo_tier"],
            -int(x["is_available_now"]),
            -x["p_availability"],
            x["fit_distance"],
            x["spot_id"],
        )
    )
    return rows


def top_capacity_metrics(df: pd.DataFrame, score_col: str, label_col: str, frac: float):
    d = df.sort_values(score_col, ascending=False).reset_index(drop=True)
    n_select = max(1, math.ceil(len(d) * frac))
    top = d.iloc[:n_select]
    base = float(d[label_col].mean())
    positives = int(d[label_col].sum())
    top_positives = int(top[label_col].sum())
    rate = top_positives / n_select
    return {
        "selected": n_select,
        "positives": top_positives,
        "rate": rate,
        "lift": rate / base if base > 0 else np.nan,
        "recall": top_positives / positives if positives > 0 else np.nan,
        "confirmed_serviceable_rate": float(top["confirmed_serviceable"].mean()),
    }


def core_metrics(df: pd.DataFrame, score_col: str, label_col: str):
    y = df[label_col].astype(int).to_numpy()
    p = df[score_col].astype(float).to_numpy()
    rank = df.sort_values(score_col, ascending=False)

    n10 = max(1, math.ceil(len(rank) * 0.10))
    n20 = max(1, math.ceil(len(rank) * 0.20))
    top10 = rank.iloc[:n10]
    top20 = rank.iloc[:n20]
    base = float(df[label_col].mean())
    positives = int(df[label_col].sum())

    return {
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1])),
        "lift_top_10pct": float((top10[label_col].mean()) / base),
        "recall_top_20pct": float(top20[label_col].sum() / positives),
    }


def main():
    leads, spots, iq, av, oof, av_rates = load_inputs()

    dyn = oof[oof["stage"].isin(["T1_first_inquiry", "T2_engaged"])].copy()
    current = iq[
        [
            "inquiry_id",
            "lead_id",
            "spot_id",
            "inquiry_at",
            "requested_area_sqm",
            "requested_budget_mxn_rent_monthly",
            "requested_budget_mxn_sale_total",
        ]
    ].copy()

    if "inquiry_id" in dyn.columns:
        current_for_merge = current.rename(columns={"spot_id": "spot_id_current"})
        dyn = dyn.merge(
            current_for_merge,
            on=["lead_id", "inquiry_id"],
            how="left",
            validate="many_to_one",
        )
        if dyn["inquiry_at"].isna().any():
            raise RuntimeError("Some OOF T1/T2 rows did not resolve by inquiry_id.")
        if not (pd.to_datetime(dyn["score_time"]) == pd.to_datetime(dyn["inquiry_at"])).all():
            raise RuntimeError("Canonical inquiry_id resolves to an inquiry_at different from score_time.")
        if "spot_id" not in dyn.columns:
            dyn["spot_id"] = dyn["spot_id_current"]
        else:
            mismatch = (
                dyn["spot_id"].notna()
                & dyn["spot_id_current"].notna()
                & (dyn["spot_id"].astype(int) != dyn["spot_id_current"].astype(int))
            )
            if mismatch.any():
                raise RuntimeError("Canonical OOF spot_id disagrees with inquiry spot_id.")
        dyn = dyn.drop(columns=["spot_id_current"])
    else:
        dyn = dyn.merge(
            current,
            left_on=["lead_id", "score_time"],
            right_on=["lead_id", "inquiry_at"],
            how="left",
            validate="many_to_one",
        )
        if dyn["inquiry_id"].isna().any():
            raise RuntimeError("Some OOF T1/T2 rows did not resolve to the current inquiry.")

    lead_lookup = leads.set_index("lead_id")
    spot_lookup = {
        int(r.spot_id): r
        for r in spots.itertuples(index=False)
    }
    spots_by_sector = {
        sector: list(g.itertuples(index=False))
        for sector, g in spots.groupby("sector_name", sort=False)
    }

    av_index = build_availability_index(av)
    sector_p, global_p = build_rate_maps(av_rates)

    all_recommendations = {}
    p_inventory = []
    confirmed = []
    current_available = []
    candidate_counts = []

    for r in dyn.itertuples(index=False):
        lead = lead_lookup.loc[int(r.lead_id)]
        current_row = pd.Series(r._asdict())

        current_snap = latest_snapshot(av_index, int(r.spot_id), pd.Timestamp(r.score_time))
        current_now = bool(current_snap and current_snap["is_available"])

        recs = rank_fallback(
            lead,
            current_row,
            pd.Timestamp(r.score_time),
            int(r.fold),
            spots_by_sector,
            spot_lookup,
            av_index,
            sector_p,
            global_p,
        )
        all_recommendations[(int(r.fold), int(r.row_id))] = recs
        candidate_counts.append(len(recs))

        top3 = recs[:K_FINAL]
        current_p = p_spot_available(
            int(r.spot_id),
            pd.Timestamp(r.score_time),
            int(r.fold),
            spot_lookup,
            av_index,
            sector_p,
            global_p,
        )
        best_p = max([current_p] + [x["p_availability"] for x in top3])
        is_confirmed = current_now or any(x["is_available_now"] for x in top3)

        p_inventory.append(best_p)
        confirmed.append(int(is_confirmed))
        current_available.append(int(current_now))

    dyn["p_inventory_top3"] = p_inventory
    dyn["confirmed_serviceable"] = confirmed
    dyn["current_spot_available"] = current_available
    dyn["fallback_candidate_count"] = candidate_counts
    dyn["joint_success"] = (
        dyn["target_30d"].astype(int) * dyn["confirmed_serviceable"].astype(int)
    )
    dyn["lead_opportunity_score"] = (
        dyn[QUALITY_COL].astype(float) * dyn["p_inventory_top3"].astype(float)
    )

    # Core joint-proxy metrics. Never mix raw rankings across folds.
    core_rows = []
    for stage in ["T1_first_inquiry", "T2_engaged"]:
        stage_metrics = {"quality_only": [], "lead_opportunity_score": []}
        for fold in sorted(dyn["fold"].unique()):
            g = dyn[(dyn["stage"] == stage) & (dyn["fold"] == fold)]
            stage_metrics["quality_only"].append(core_metrics(g, QUALITY_COL, "joint_success"))
            stage_metrics["lead_opportunity_score"].append(
                core_metrics(g, "lead_opportunity_score", "joint_success")
            )

        for variant, vals in stage_metrics.items():
            row = {"stage": stage, "variant": variant}
            for metric in vals[0]:
                row[metric] = float(np.mean([x[metric] for x in vals]))
            core_rows.append(row)

    core_df = pd.DataFrame(core_rows)
    macro = (
        core_df.groupby("variant", as_index=False)
        .agg(
            roc_auc=("roc_auc", "mean"),
            average_precision=("average_precision", "mean"),
            brier=("brier", "mean"),
            log_loss=("log_loss", "mean"),
            lift_top_10pct=("lift_top_10pct", "mean"),
            recall_top_20pct=("recall_top_20pct", "mean"),
        )
        .assign(stage="MACRO")
    )
    core_out = pd.concat([core_df, macro[core_df.columns]], ignore_index=True)
    core_out.to_csv(OUT / "joint_core_metrics_reproduced.csv", index=False)

    # P85 capacity: joint objective + conversion-only guardrail.
    cap_rows = []
    for fold in sorted(dyn["fold"].unique()):
        for stage in ["T1_first_inquiry", "T2_engaged"]:
            g = dyn[(dyn["fold"] == fold) & (dyn["stage"] == stage)]
            for variant, col in [
                ("quality_only", QUALITY_COL),
                ("lead_opportunity_score", "lead_opportunity_score"),
            ]:
                joint = top_capacity_metrics(g, col, "joint_success", CAPACITY)
                conv = top_capacity_metrics(g, col, "target_30d", CAPACITY)
                cap_rows.append(
                    {
                        "fold": int(fold),
                        "stage": stage,
                        "variant": variant,
                        "joint_lift_at_15": joint["lift"],
                        "joint_recall_at_15": joint["recall"],
                        "joint_positives_at_15": joint["positives"],
                        "conversion_lift_at_15": conv["lift"],
                        "conversion_recall_at_15": conv["recall"],
                        "conversion_positives_at_15": conv["positives"],
                        "confirmed_serviceable_rate_at_15": joint[
                            "confirmed_serviceable_rate"
                        ],
                    }
                )
    pd.DataFrame(cap_rows).to_csv(
        OUT / "joint_capacity_metrics_reproduced.csv", index=False
    )

    # Fallback K selection on folds 1-3 and confirmation on fold 4.
    fb_rows = []
    for fold in sorted(dyn["fold"].unique()):
        g = dyn[(dyn["fold"] == fold) & (dyn["current_spot_available"] == 0)]
        counts = g["fallback_candidate_count"].to_numpy()
        fb_rows.append(
            {
                "fold": int(fold),
                "cases": len(g),
                "coverage_any": float(np.mean(counts >= 1)),
                "full_3": float(np.mean(counts >= 3)),
                "full_5": float(np.mean(counts >= 5)),
                "no_result": float(np.mean(counts == 0)),
            }
        )
    pd.DataFrame(fb_rows).to_csv(OUT / "fallback_by_fold_reproduced.csv", index=False)

    # Final-fold recommendation quality.
    f4 = dyn[(dyn["fold"] == 4) & (dyn["current_spot_available"] == 0)]
    returned = []
    full3_corridor = 0
    available_fallback_cases = 0

    for r in f4.itertuples(index=False):
        recs = all_recommendations[(int(r.fold), int(r.row_id))]
        top3 = recs[:3]
        returned.extend(top3)
        if len(top3) == 3 and top3[2]["geo_tier"] == 0:
            full3_corridor += 1
        if any(x["is_available_now"] for x in top3):
            available_fallback_cases += 1

    summary = {
        "fallback_cases": int(len(f4)),
        "coverage_at_3_any": float((f4["fallback_candidate_count"] >= 1).mean()),
        "full_list_at_3": float((f4["fallback_candidate_count"] >= 3).mean()),
        "full_list_at_5": float((f4["fallback_candidate_count"] >= 5).mean()),
        "no_result_rate": float((f4["fallback_candidate_count"] == 0).mean()),
        "available_fallback_at_3": float(available_fallback_cases / len(f4)),
        "median_valid_candidates": float(f4["fallback_candidate_count"].median()),
        "all_three_same_corridor_given_full_list_3": float(
            full3_corridor / max(1, int((f4["fallback_candidate_count"] >= 3).sum()))
        ),
        "returned_recommendations": len(returned),
        "currently_available_recommendation_share": float(
            np.mean([x["is_available_now"] for x in returned]) if returned else np.nan
        ),
        "strict_recommendation_share": float(
            np.mean([x["strict"] for x in returned]) if returned else np.nan
        ),
    }
    (OUT / "fallback_fold4_reproduced.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    # Final P85 business count: how many joint positives are gained?
    final_rows = []
    for stage in ["T1_first_inquiry", "T2_engaged"]:
        g = dyn[(dyn["fold"] == 4) & (dyn["stage"] == stage)]
        for variant, col in [
            ("quality_only", QUALITY_COL),
            ("lead_opportunity_score", "lead_opportunity_score"),
        ]:
            joint = top_capacity_metrics(g, col, "joint_success", CAPACITY)
            conv = top_capacity_metrics(g, col, "target_30d", CAPACITY)
            final_rows.append(
                {
                    "stage": stage,
                    "variant": variant,
                    "selected": joint["selected"],
                    "joint_positives": joint["positives"],
                    "conversion_positives": conv["positives"],
                    "confirmed_serviceable_rate": joint[
                        "confirmed_serviceable_rate"
                    ],
                }
            )
    final_df = pd.DataFrame(final_rows)
    final_df.to_csv(OUT / "final_fold_p85_reproduced.csv", index=False)

    # Score distribution in fold 4.
    quant_rows = []
    for stage, g in [
        ("ALL", dyn[dyn["fold"] == 4]),
        ("T1_first_inquiry", dyn[(dyn["fold"] == 4) & (dyn["stage"] == "T1_first_inquiry")]),
        ("T2_engaged", dyn[(dyn["fold"] == 4) & (dyn["stage"] == "T2_engaged")]),
    ]:
        for component, col in [
            ("lead_quality", QUALITY_COL),
            ("inventory_availability", "p_inventory_top3"),
            ("lead_opportunity_score", "lead_opportunity_score"),
        ]:
            q = g[col].quantile([0.05, 0.25, 0.50, 0.75, 0.95])
            quant_rows.append(
                {
                    "stage": stage,
                    "component": component,
                    "p05": float(q.loc[0.05]),
                    "p25": float(q.loc[0.25]),
                    "p50": float(q.loc[0.50]),
                    "p75": float(q.loc[0.75]),
                    "p95": float(q.loc[0.95]),
                }
            )
    pd.DataFrame(quant_rows).to_csv(
        OUT / "score_distribution_fold4_reproduced.csv", index=False
    )

    print(core_out.to_string(index=False))
    print(pd.DataFrame(cap_rows).to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
