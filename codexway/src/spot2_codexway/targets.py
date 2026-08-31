from __future__ import annotations

import numpy as np
import pandas as pd

from .contracts import Settings


def first_inquiries(inquiries: pd.DataFrame) -> pd.DataFrame:
    ordered = inquiries.sort_values(["lead_id", "inquiry_at", "inquiry_id"], kind="mergesort")
    result = ordered.drop_duplicates("lead_id", keep="first").copy()
    if not result["lead_id"].is_unique:
        raise AssertionError("T1 grain must be one row per lead")
    return result


def add_t1_target(first: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    result = first.copy()
    maturity_cutoff = settings.evaluation_cutoff_exclusive - pd.Timedelta(days=settings.maturity_days)
    mature = result["inquiry_at"] < maturity_cutoff
    result["target_t1"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result.loc[mature, "target_t1"] = result.loc[mature, "broker_response"].eq("scheduled_visit").astype(int)
    result["target_mature"] = mature
    result["target_maturity_cutoff"] = maturity_cutoff
    return result


def build_t0_target(leads: pd.DataFrame, inquiries: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    base = leads[["lead_id", "created_at"]].copy()
    events = inquiries[["lead_id", "inquiry_at", "broker_response"]].merge(base, on="lead_id", how="left", validate="many_to_one")
    horizon = pd.Timedelta(days=settings.t0_horizon_days)
    in_window = events["inquiry_at"].gt(events["created_at"]) & events["inquiry_at"].le(events["created_at"] + horizon)
    events = events[in_window]
    positive = events[events["broker_response"].eq("scheduled_visit")].groupby("lead_id").size().gt(0)
    mature = base["created_at"] < settings.evaluation_cutoff_exclusive - horizon
    base["target_t0_30d"] = pd.Series(pd.NA, index=base.index, dtype="Int64")
    base.loc[mature, "target_t0_30d"] = base.loc[mature, "lead_id"].map(positive).eq(True).astype(int)
    base["target_mature"] = mature
    return base


def add_t2_target(inquiries: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    ordered = inquiries.sort_values(["lead_id", "inquiry_at", "inquiry_id"], kind="mergesort").copy()
    ordered["inquiry_number"] = ordered.groupby("lead_id").cumcount() + 1
    result = ordered[ordered["inquiry_number"] >= 2].copy()
    maturity_cutoff = settings.evaluation_cutoff_exclusive - pd.Timedelta(days=settings.maturity_days)
    mature = result["inquiry_at"] < maturity_cutoff
    result["target_t2"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result.loc[mature, "target_t2"] = result.loc[mature, "broker_response"].eq("scheduled_visit").astype(int)
    result["target_mature"] = mature
    return result


def sensitivity_targets(first: pd.DataFrame, inquiries: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    result = first[["lead_id", "inquiry_id", "inquiry_at", "broker_response"]].copy()
    for days in (7, 14, 30):
        cutoff = settings.evaluation_cutoff_exclusive - pd.Timedelta(days=days)
        mature = result["inquiry_at"] < cutoff
        result[f"mature_{days}d"] = mature
        result[f"scheduled_first_{days}d"] = np.where(mature, result["broker_response"].eq("scheduled_visit"), np.nan)
    main_mature = result["inquiry_at"] < settings.evaluation_cutoff_exclusive - pd.Timedelta(days=settings.maturity_days)
    result["accepted_or_scheduled"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result.loc[main_mature, "accepted_or_scheduled"] = result.loc[
        main_mature, "broker_response"
    ].isin(["accepted", "scheduled_visit"]).astype(int)
    joined = inquiries[["lead_id", "inquiry_at", "broker_response"]].merge(
        result[["lead_id", "inquiry_at"]].rename(columns={"inquiry_at": "first_inquiry_at"}),
        on="lead_id",
        how="left",
        validate="many_to_one",
    )
    within = joined["inquiry_at"].between(joined["first_inquiry_at"], joined["first_inquiry_at"] + pd.Timedelta(days=30), inclusive="both")
    any30 = joined[within & joined["broker_response"].eq("scheduled_visit")].groupby("lead_id").size().gt(0)
    exposure30 = joined[within].groupby("lead_id").size()
    mature30 = result["inquiry_at"] < settings.evaluation_cutoff_exclusive - pd.Timedelta(days=30)
    result["any_scheduled_inquiry_30d"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result.loc[mature30, "any_scheduled_inquiry_30d"] = result.loc[mature30, "lead_id"].map(any30).eq(True).astype(int)
    result["inquiry_exposure_30d"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result.loc[mature30, "inquiry_exposure_30d"] = result.loc[mature30, "lead_id"].map(exposure30).fillna(0).astype(int)
    return result
