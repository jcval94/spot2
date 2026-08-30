from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

HORIZON_DAYS = 30
TARGET_NAME = "target_scheduled_visit_30d"
AB_OUTCOME_NAME = "lead_scheduled_visit_30d_from_assignment"


@dataclass(frozen=True)
class TargetContract:
    event_value: str = "scheduled_visit"
    horizon_days: int = HORIZON_DAYS
    interval: str = "(anchor, anchor + 30d]"
    timezone: str = "UTC"
    positive_value: int = 1
    negative_value: int = 0
    ambiguous_value: str = "AMBIGUOUS"


CONTRACT = TargetContract()


def prepare_candidate_events(inquiries: pd.DataFrame) -> pd.DataFrame:
    """Candidate-data adapter only.

    The candidate package does not contain an actual response timestamp.
    It is reconstructed from inquiry_at + broker_response_hours when the
    latter exists. Production E028 MUST log the actual backend event time.
    """
    d = inquiries.copy()
    d["inquiry_at"] = pd.to_datetime(d["inquiry_at"], errors="coerce")
    hours = pd.to_numeric(d["broker_response_hours"], errors="coerce")
    d["response_event_at"] = d["inquiry_at"] + pd.to_timedelta(hours, unit="h")
    d.loc[hours.isna(), "response_event_at"] = pd.NaT
    d["response_event_time_observed"] = d["response_event_at"].notna()
    return d


def label_scoring_snapshots(
    snapshots: pd.DataFrame,
    inquiries: pd.DataFrame,
    *,
    lead_col: str = "lead_id",
    anchor_col: str = "score_time",
    observation_end: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Apply the definitive offline target contract.

    Output rows have:
      - target_scheduled_visit_30d: 1, 0 or NaN
      - target_status:
          POSITIVE
          NEGATIVE
          AMBIGUOUS_UNKNOWN_EVENT_TIME
          INELIGIBLE_PRIOR_SCHEDULED_VISIT
          RIGHT_CENSORED

    A missing event timestamp is never silently converted to a negative.
    """
    events = prepare_candidate_events(inquiries)
    scheduled = events[events["broker_response"].eq(CONTRACT.event_value)].copy()

    if observation_end is None:
        candidates = [
            events["inquiry_at"].max(),
            events["response_event_at"].max(),
        ]
        observation_end = max(x for x in candidates if pd.notna(x))
    observation_end = pd.Timestamp(observation_end)
    cutoff = observation_end - pd.Timedelta(days=CONTRACT.horizon_days)

    known_map: dict[object, np.ndarray] = {}
    unknown_map: dict[object, np.ndarray] = {}
    for lead_id, g in scheduled.groupby(lead_col):
        known = g.loc[g["response_event_at"].notna(), "response_event_at"]
        unknown = g.loc[g["response_event_at"].isna(), "inquiry_at"]
        known_map[lead_id] = np.sort(known.to_numpy(dtype="datetime64[ns]"))
        unknown_map[lead_id] = np.sort(unknown.to_numpy(dtype="datetime64[ns]"))

    out = snapshots.copy()
    targets: list[float] = []
    statuses: list[str] = []

    for row in out.itertuples(index=False):
        lead_id = getattr(row, lead_col)
        anchor_raw = getattr(row, anchor_col)
        if pd.isna(anchor_raw):
            targets.append(np.nan)
            statuses.append("RIGHT_CENSORED")
            continue

        anchor = pd.Timestamp(anchor_raw)
        if anchor > cutoff:
            targets.append(np.nan)
            statuses.append("RIGHT_CENSORED")
            continue

        start = np.datetime64(anchor.to_datetime64())
        end = np.datetime64((anchor + pd.Timedelta(days=CONTRACT.horizon_days)).to_datetime64())

        known = known_map.get(lead_id, np.asarray([], dtype="datetime64[ns]"))
        # Any already-observed scheduled visit makes this scoring snapshot ineligible.
        if len(known) and np.any(known <= start):
            targets.append(np.nan)
            statuses.append("INELIGIBLE_PRIOR_SCHEDULED_VISIT")
            continue

        # A known future event inside the horizon proves a positive regardless
        # of any additional unknown-time events.
        pos = int(np.searchsorted(known, start, side="right"))
        if pos < len(known) and known[pos] <= end:
            targets.append(1.0)
            statuses.append("POSITIVE")
            continue

        unknown = unknown_map.get(lead_id, np.asarray([], dtype="datetime64[ns]"))
        # Since response must happen after inquiry_at, an unknown-time scheduled
        # event whose inquiry began on/before the horizon end could have landed
        # inside the window (or even before anchor). Its exact label is unknown.
        if len(unknown) and np.any(unknown <= end):
            targets.append(np.nan)
            statuses.append("AMBIGUOUS_UNKNOWN_EVENT_TIME")
            continue

        targets.append(0.0)
        statuses.append("NEGATIVE")

    out[TARGET_NAME] = targets
    out["target_status"] = statuses
    out["target_observation_end"] = observation_end
    out["target_maturity_cutoff"] = cutoff
    return out


def build_lead_ab_outcome(
    leads: pd.DataFrame,
    inquiries: pd.DataFrame,
    *,
    assignment_col: str = "assignment_at",
) -> pd.DataFrame:
    """Build the lead-level retrospective analogue of the E028 primary outcome.

    In prospective production, actual backend response_event_at is mandatory
    and AMBIGUOUS should be zero except for instrumentation failures.
    """
    base = leads.copy()
    if assignment_col not in base:
        raise KeyError(f"{assignment_col} is required")
    labeled = label_scoring_snapshots(
        base.rename(columns={assignment_col: "score_time"}),
        inquiries,
        anchor_col="score_time",
    )
    labeled[AB_OUTCOME_NAME] = labeled[TARGET_NAME]
    return labeled
