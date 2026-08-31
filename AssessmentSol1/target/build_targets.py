"""Frozen target construction for AssessmentSol1 P2.

This module defines labels only. It trains no model, computes no predictive
performance metric, and must never be imported as a feature source.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import polars as pl

PRIMARY_TARGET_ID = "T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1"
PRIMARY_STAGE = "T1"
PRIMARY_MATURITY_DAYS = 14
TARGET_B_HORIZON_DAYS = 30
TARGET_C_HORIZON_DAYS = 30
MATURITY_BUFFERS = (7, 14, 30)
SCHEDULED = "scheduled_visit"
OUTCOME_ONLY_FIELDS = frozenset({"broker_response", "broker_response_hours"})


def _parse_dt(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_raw(repo_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Read canonical Parquet only; CSV is not used in target construction."""
    root = repo_root / "data" / "candidate" / "parquet"
    leads = pl.read_parquet(root / "leads.parquet").to_dicts()
    inquiries = pl.read_parquet(root / "inquiries.parquet").to_dicts()
    return leads, inquiries


def group_inquiries(
    inquiries: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw in inquiries:
        row = dict(raw)
        row["_t"] = _parse_dt(row["inquiry_at"])
        grouped[int(row["lead_id"])].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda r: (r["_t"], int(r["inquiry_id"])))
    return dict(grouped)


def first_inquiry(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Earliest inquiry_at, then smallest inquiry_id as deterministic tie-break."""
    if not rows:
        raise ValueError("Lead has no inquiries")
    return min(rows, key=lambda r: (_parse_dt(r["inquiry_at"]), int(r["inquiry_id"])))


def activity_horizon(inquiries: list[dict[str, Any]]) -> datetime:
    """Conservative maturity anchor because raw extraction time is absent."""
    return max(_parse_dt(r["inquiry_at"]) for r in inquiries)


def is_mature(score_time: datetime, horizon: datetime, buffer_days: int) -> bool:
    return score_time + timedelta(days=buffer_days) <= horizon


def target_a(first: dict[str, Any]) -> tuple[str, int | None]:
    """First-inquiry eventual recorded status; broker_response_hours is ignored."""
    status = first.get("broker_response")
    if status is None or str(status) == "":
        return "AMBIGUOUS_MISSING_RESPONSE_STATUS", None
    return "LABELED", int(status == SCHEDULED)


def _response_event_at(row: dict[str, Any]) -> datetime | None:
    hours = row.get("broker_response_hours")
    if hours is None:
        return None
    try:
        hours_f = float(hours)
    except (TypeError, ValueError):
        return None
    if hours_f < 0:
        return None
    return _parse_dt(row["inquiry_at"]) + timedelta(hours=hours_f)


def target_b(
    rows: list[dict[str, Any]],
    score_time: datetime,
    horizon: datetime,
    extra_maturity_days: int = 0,
) -> dict[str, Any]:
    """E028-style scheduled_visit within 30d using reconstructed response_event_at.

    Boundary is (score_time, score_time + 30d]. Untimed scheduled_visit rows
    whose inquiry starts inside the window create ambiguity unless a timed
    positive already proves the label.
    """
    end = score_time + timedelta(days=TARGET_B_HORIZON_DAYS)
    if end + timedelta(days=extra_maturity_days) > horizon:
        return {
            "status": "CENSORED",
            "label": None,
            "positive_inquiry_id": None,
            "positive_response_event_at": None,
            "ambiguous_untimed_scheduled_count": 0,
            "timed_scheduled_count": 0,
        }

    positive: tuple[datetime, int] | None = None
    ambiguous = 0
    timed = 0
    for row in rows:
        if row.get("broker_response") != SCHEDULED:
            continue
        inquiry_time = _parse_dt(row["inquiry_at"])
        event_time = _response_event_at(row)
        if event_time is None:
            if score_time <= inquiry_time <= end:
                ambiguous += 1
            continue
        timed += 1
        if score_time < event_time <= end:
            candidate = (event_time, int(row["inquiry_id"]))
            if positive is None or candidate < positive:
                positive = candidate

    if positive is not None:
        return {
            "status": "LABELED",
            "label": 1,
            "positive_inquiry_id": positive[1],
            "positive_response_event_at": positive[0],
            "ambiguous_untimed_scheduled_count": ambiguous,
            "timed_scheduled_count": timed,
        }
    if ambiguous:
        return {
            "status": "AMBIGUOUS",
            "label": None,
            "positive_inquiry_id": None,
            "positive_response_event_at": None,
            "ambiguous_untimed_scheduled_count": ambiguous,
            "timed_scheduled_count": timed,
        }
    return {
        "status": "LABELED",
        "label": 0,
        "positive_inquiry_id": None,
        "positive_response_event_at": None,
        "ambiguous_untimed_scheduled_count": 0,
        "timed_scheduled_count": timed,
    }


def target_c(
    rows: list[dict[str, Any]],
    score_time: datetime,
    horizon: datetime,
    maturity_buffer_days: int,
    inquiry_horizon_days: int = TARGET_C_HORIZON_DAYS,
) -> dict[str, Any]:
    """Lead progress: inquiry initiated in [t, t+H] eventually is scheduled_visit.

    This does NOT claim the visit was scheduled inside H days.
    """
    end = score_time + timedelta(days=inquiry_horizon_days)
    if end + timedelta(days=maturity_buffer_days) > horizon:
        return {
            "status": "CENSORED",
            "label": None,
            "positive_inquiry_id": None,
            "positive_inquiry_at": None,
        }

    positive: tuple[datetime, int] | None = None
    missing_status = False
    for row in rows:
        inquiry_time = _parse_dt(row["inquiry_at"])
        if not (score_time <= inquiry_time <= end):
            continue
        status = row.get("broker_response")
        if status is None or str(status) == "":
            missing_status = True
        elif status == SCHEDULED:
            candidate = (inquiry_time, int(row["inquiry_id"]))
            if positive is None or candidate < positive:
                positive = candidate

    if positive is not None:
        return {
            "status": "LABELED",
            "label": 1,
            "positive_inquiry_id": positive[1],
            "positive_inquiry_at": positive[0],
        }
    if missing_status:
        return {
            "status": "AMBIGUOUS",
            "label": None,
            "positive_inquiry_id": None,
            "positive_inquiry_at": None,
        }
    return {
        "status": "LABELED",
        "label": 0,
        "positive_inquiry_id": None,
        "positive_inquiry_at": None,
    }


def assert_outcome_fields_not_features(feature_columns: list[str]) -> None:
    leaked = OUTCOME_ONLY_FIELDS.intersection(feature_columns)
    if leaked:
        raise AssertionError(f"Outcome-only fields cannot be features: {sorted(leaked)}")


def build_t1_audit(
    leads: list[dict[str, Any]], inquiries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped = group_inquiries(inquiries)
    lead_lookup = {int(r["lead_id"]): r for r in leads}
    horizon = activity_horizon(inquiries)
    output: list[dict[str, Any]] = []

    for lead_id in sorted(grouped):
        rows = grouped[lead_id]
        first = first_inquiry(rows)
        score_time = _parse_dt(first["inquiry_at"])
        a_status, a_label = target_a(first)
        b = target_b(rows, score_time, horizon, extra_maturity_days=0)
        c14 = target_c(rows, score_time, horizon, maturity_buffer_days=14)
        lead = lead_lookup[lead_id]

        output.append(
            {
                "lead_id": lead_id,
                "lead_created_at": lead["created_at"],
                "score_inquiry_id": int(first["inquiry_id"]),
                "score_time": first["inquiry_at"],
                "first_broker_response": first.get("broker_response"),
                "first_broker_response_hours": first.get("broker_response_hours"),
                "inquiry_count": len(rows),
                "last_inquiry_at": rows[-1]["inquiry_at"],
                "a_eventual_first_scheduled_visit": a_label,
                "a_mature_7": is_mature(score_time, horizon, 7),
                "a_mature_14": is_mature(score_time, horizon, 14),
                "a_mature_30": is_mature(score_time, horizon, 30),
                "primary_t1_eligible": (
                    a_status == "LABELED" and is_mature(score_time, horizon, 14)
                ),
                "primary_t1_label": (
                    a_label
                    if a_status == "LABELED"
                    and is_mature(score_time, horizon, 14)
                    else None
                ),
                "b30_status": b["status"],
                "b30_label": b["label"],
                "b30_positive_inquiry_id": b["positive_inquiry_id"],
                "b30_positive_response_event_at": _iso(
                    b["positive_response_event_at"]
                ),
                "b30_ambiguous_untimed_scheduled_count": (
                    b["ambiguous_untimed_scheduled_count"]
                ),
                "b30_timed_scheduled_count": b["timed_scheduled_count"],
                "c30_status_maturity14": c14["status"],
                "c30_label_maturity14": c14["label"],
                "c30_positive_inquiry_id": c14["positive_inquiry_id"],
                "c30_positive_inquiry_at": _iso(c14["positive_inquiry_at"]),
                "c30_mature_7": is_mature(score_time, horizon, 30 + 7),
                "c30_mature_14": is_mature(score_time, horizon, 30 + 14),
                "c30_mature_30": is_mature(score_time, horizon, 30 + 30),
            }
        )
    return output


def _monthly_stability(
    labeled: list[tuple[datetime, int]],
) -> dict[str, float | int]:
    by_month: dict[str, list[int]] = defaultdict(list)
    for score_time, label in labeled:
        by_month[score_time.strftime("%Y-%m")].append(label)
    rates = [
        sum(values) / len(values)
        for values in by_month.values()
        if len(values) >= 50
    ]
    if not rates:
        return {
            "months_ge_50": 0,
            "monthly_prevalence_sd_pp": 0.0,
            "monthly_prevalence_range_pp": 0.0,
        }
    return {
        "months_ge_50": len(rates),
        "monthly_prevalence_sd_pp": pstdev(rates) * 100,
        "monthly_prevalence_range_pp": (max(rates) - min(rates)) * 100,
    }


def summarize_config(
    target_option: str,
    grouped: dict[int, list[dict[str, Any]]],
    horizon: datetime,
    maturity_buffer_days: int,
) -> dict[str, Any]:
    labeled: list[tuple[datetime, int]] = []
    ambiguous = 0
    censored = 0

    for rows in grouped.values():
        first = first_inquiry(rows)
        score_time = _parse_dt(first["inquiry_at"])

        if target_option == "A":
            if not is_mature(score_time, horizon, maturity_buffer_days):
                censored += 1
                continue
            status, label = target_a(first)
            if status != "LABELED":
                ambiguous += 1
                continue
        elif target_option == "B":
            result = target_b(
                rows, score_time, horizon,
                extra_maturity_days=maturity_buffer_days,
            )
            if result["status"] == "CENSORED":
                censored += 1
                continue
            if result["status"] == "AMBIGUOUS":
                ambiguous += 1
                continue
            label = result["label"]
        elif target_option == "C":
            result = target_c(
                rows, score_time, horizon,
                maturity_buffer_days=maturity_buffer_days,
            )
            if result["status"] == "CENSORED":
                censored += 1
                continue
            if result["status"] == "AMBIGUOUS":
                ambiguous += 1
                continue
            label = result["label"]
        else:
            raise ValueError(target_option)

        assert label in (0, 1)
        labeled.append((score_time, int(label)))

    positives = sum(label for _, label in labeled)
    total = len(grouped)
    semantics = {
        "A": "first inquiry eventually recorded scheduled_visit",
        "B": "timed scheduled_visit event in (score_time, score_time+30d]",
        "C": "an inquiry initiated within 30d eventually recorded scheduled_visit",
    }[target_option]
    result = {
        "target_option": target_option,
        "stage": "T1",
        "horizon_days": (
            None if target_option == "A" else 30
        ),
        "maturity_buffer_days": maturity_buffer_days,
        "semantics": semantics,
        "total": total,
        "labeled": len(labeled),
        "positive": positives,
        "negative": len(labeled) - positives,
        "ambiguous": ambiguous,
        "censored": censored,
        "cohort_coverage": len(labeled) / total,
        "prevalence": positives / len(labeled),
    }
    result.update(_monthly_stability(labeled))
    return result


def build_cohort_summary(
    inquiries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped = group_inquiries(inquiries)
    horizon = activity_horizon(inquiries)
    rows = [
        summarize_config("A", grouped, horizon, buffer)
        for buffer in MATURITY_BUFFERS
    ]
    rows += [
        summarize_config("B", grouped, horizon, buffer)
        for buffer in (0, 7, 14, 30)
    ]
    rows += [
        summarize_config("C", grouped, horizon, buffer)
        for buffer in MATURITY_BUFFERS
    ]
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("No rows")
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()

    leads, inquiries = read_raw(root)
    audit = build_t1_audit(leads, inquiries)
    cohort = build_cohort_summary(inquiries)

    primary = next(
        row for row in cohort
        if row["target_option"] == "A"
        and row["maturity_buffer_days"] == PRIMARY_MATURITY_DAYS
    )
    contract = json.loads(
        (root / "AssessmentSol1" / "target" / "target_contract.json").read_text(
            encoding="utf-8"
        )
    )
    timed_realized = [
        float(r["broker_response_hours"])
        for r in inquiries
        if r.get("broker_response") in {"accepted", "rejected", "scheduled_visit"}
        and r.get("broker_response_hours") is not None
    ]
    scheduled = [r for r in inquiries if r.get("broker_response") == SCHEDULED]
    scheduled_timed = [
        r for r in scheduled if r.get("broker_response_hours") is not None
    ]
    result = {
        "phase": "PROMPT_2",
        "decision_rule": (
            "No model performance metric was computed or used. Decision uses "
            "business semantics, temporal identifiability, label coverage, "
            "prevalence stability, censoring, and implementation feasibility."
        ),
        "activity_horizon": _iso(activity_horizon(inquiries)),
        "primary_target": {
            "id": PRIMARY_TARGET_ID,
            "stage": PRIMARY_STAGE,
            "maturity_buffer_days": PRIMARY_MATURITY_DAYS,
            "audit": primary,
            "freeze": True,
            "immutable_due_to_future_model_performance": True,
        },
        "cohort_summary": cohort,
        "response_timing_audit": {
            "scheduled_visit_rows": len(scheduled),
            "scheduled_visit_with_hours": len(scheduled_timed),
            "scheduled_visit_missing_hours": len(scheduled) - len(scheduled_timed),
            "scheduled_visit_timing_coverage": (
                len(scheduled_timed) / len(scheduled)
            ),
            "realized_timed_rows": len(timed_realized),
            "realized_response_hours_max": max(timed_realized),
            "realized_timed_within_7d_rate": (
                sum(h <= 168 for h in timed_realized) / len(timed_realized)
            ),
        },
        "secondary_targets": contract["secondary_targets"],
        "no_model_metrics": {
            "AUC": "NOT_COMPUTED",
            "AP": "NOT_COMPUTED",
            "Lift": "NOT_COMPUTED",
        },
    }

    if args.write:
        target_dir = root / "AssessmentSol1" / "target"
        write_csv(target_dir / "target_audit.csv", audit)
        write_csv(target_dir / "target_cohort_summary.csv", cohort)
        (target_dir / "target_summary.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
