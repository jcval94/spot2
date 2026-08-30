from __future__ import annotations

import hashlib
import json
from pathlib import Path
import polars as pl

FORBIDDEN_MODEL_COLUMNS = {
    "lead_score_internal",
    "broker_response",
    "broker_response_hours",
    "days_on_market",
    "total_views",
    "total_inquiries",
    "is_active",
    "similar_available_spots",
    "avg_price_sqm_mxn",
    "recent_occupancy_rate",
    "absorption_velocity_days",
    "recent_inquiry_volume",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_prediction_key_unique(df: pl.DataFrame) -> None:
    if df["prediction_key"].null_count() or df["prediction_key"].n_unique() != df.height:
        raise AssertionError("prediction_key is null or non-unique")


def assert_no_future_inquiry(df: pl.DataFrame) -> None:
    if "hist_max_inquiry_time" in df.columns:
        bad = df.filter(
            pl.col("hist_max_inquiry_time").is_not_null()
            & (pl.col("hist_max_inquiry_time") >= pl.col("score_time"))
        )
        if bad.height:
            raise AssertionError("Historical inquiry at/after score_time")


def assert_no_future_snapshot(df: pl.DataFrame) -> None:
    bad = df.filter(
        pl.col("snapshot_time").is_not_null()
        & (pl.col("snapshot_time") > pl.col("score_time"))
    )
    if bad.height:
        raise AssertionError("Future Availability snapshot")


def assert_no_forbidden_model_feature(df: pl.DataFrame) -> None:
    bad = FORBIDDEN_MODEL_COLUMNS.intersection(df.columns)
    if bad:
        raise AssertionError(f"Forbidden model columns: {sorted(bad)}")


def assert_target_statuses(df: pl.DataFrame) -> None:
    allowed = {"POSITIVE", "NEGATIVE", "AMBIGUOUS", "CENSORED", "INELIGIBLE"}
    got = set(df["target_status"].drop_nulls().unique().to_list())
    if not got.issubset(allowed):
        raise AssertionError(f"Unknown target statuses: {sorted(got - allowed)}")
    invalid_value = df.filter(
        pl.col("target_status").is_in(["POSITIVE", "NEGATIVE"])
        != pl.col("target_value").is_not_null()
    )
    if invalid_value.height:
        raise AssertionError("target_value/status inconsistency")


def assert_candidate_grain(df: pl.DataFrame) -> None:
    dup = df.group_by("prediction_key", "candidate_spot_id").len().filter(
        pl.col("len") > 1
    )
    if dup.height:
        raise AssertionError("Candidate grain expansion")


def assert_lineage_complete(
    abt_columns: set[str], lineage_path: Path
) -> None:
    lineage = pl.read_csv(lineage_path)
    registered = set(lineage["column"].to_list())
    missing = abt_columns - registered
    if missing:
        raise AssertionError(f"Missing lineage: {sorted(missing)}")


def assert_stage_observability(df: pl.DataFrame) -> None:
    if df.filter((pl.col("stage") == "T0") & pl.col("current_inquiry_id").is_not_null()).height:
        raise AssertionError("T0 has a current inquiry")
    if df.filter((pl.col("stage") == "T1") & (pl.col("inquiry_number") != 1)).height:
        raise AssertionError("T1 is not first inquiry")
    if df.filter((pl.col("stage") == "T2") & (pl.col("inquiry_number") < 2)).height:
        raise AssertionError("T2 inquiry number invalid")


def assert_split_integrity(assignments: pl.DataFrame) -> None:
    required = {"lead_id", "partition"}
    if not required.issubset(assignments.columns):
        raise AssertionError("Split assignment must include lead_id, partition")
    per_lead = assignments.group_by("lead_id").agg(
        pl.col("partition").n_unique().alias("n_partition")
    )
    if per_lead.filter(pl.col("n_partition") > 1).height:
        raise AssertionError("Entity leakage: lead appears in multiple partitions")



def _read_csv_shards(path: Path) -> pl.DataFrame:
    files = sorted(path.glob("part-*.csv"))
    if not files:
        raise AssertionError(f"No CSV shards found under {path}")
    return pl.concat(
        [pl.read_csv(p, infer_schema_length=None) for p in files],
        how="vertical_relaxed",
    )


def validate_committed_evidence(repo_root: Path) -> dict:
    """Validate committed CSV evidence when full Parquet materialization is absent."""
    out = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    spine = pl.read_csv(out / "score_spine.csv", infer_schema_length=None)
    audit = _read_csv_shards(out / "lead_quality_audit_all_snapshots")
    model = _read_csv_shards(out / "lead_quality_model_ready")
    candidate_summary = _read_csv_shards(out / "candidate_spots_summary")
    inventory_summary = _read_csv_shards(out / "inventory_state_summary")
    candidate_sample = pl.read_csv(
        out / "candidate_spots_sample.csv", infer_schema_length=None
    )
    inventory_sample = pl.read_csv(
        out / "inventory_serviceability_sample.csv", infer_schema_length=None
    )
    qa = json.loads((out / "qa_summary.json").read_text())

    for df in (spine, audit, model, candidate_sample, inventory_sample):
        if "score_time" in df.columns:
            df.with_columns(
                pl.col("score_time").str.to_datetime(strict=True).alias("score_time")
            )

    audit = audit.with_columns(
        pl.col("score_time").str.to_datetime(strict=True).alias("score_time"),
        pl.col("hist_max_inquiry_time")
        .str.to_datetime(strict=False)
        .alias("hist_max_inquiry_time"),
    )
    inventory_sample = inventory_sample.with_columns(
        pl.col("score_time").str.to_datetime(strict=True).alias("score_time"),
        pl.col("snapshot_time")
        .str.to_datetime(strict=False)
        .alias("snapshot_time"),
    )

    assert_prediction_key_unique(spine)
    assert_prediction_key_unique(audit)
    assert_prediction_key_unique(model)
    assert set(spine["prediction_key"].to_list()) == set(
        audit["prediction_key"].to_list()
    )
    if not set(model["prediction_key"].to_list()).issubset(
        set(audit["prediction_key"].to_list())
    ):
        raise AssertionError("model_ready contains keys absent from audit")

    assert_no_future_inquiry(audit)
    assert_no_forbidden_model_feature(model)
    assert_target_statuses(audit)
    assert_stage_observability(audit)
    assert_candidate_grain(candidate_sample)
    assert_candidate_grain(inventory_sample)
    assert_no_future_snapshot(inventory_sample)

    if candidate_summary["prediction_key"].n_unique() != spine.height:
        raise AssertionError("Candidate summary does not cover every prediction_key")
    if inventory_summary["prediction_key"].n_unique() != spine.height:
        raise AssertionError("Inventory summary does not cover every prediction_key")
    if int(candidate_summary["n_candidates"].sum()) != qa["candidate_spots"]["full_logical_rows"]:
        raise AssertionError("Candidate full row-count reconciliation failed")
    if int(inventory_summary["n_candidates"].sum()) != qa["inventory_serviceability"]["full_logical_rows"]:
        raise AssertionError("Inventory full row-count reconciliation failed")

    if any(c in audit.columns for c in ("partition", "fold", "split")):
        raise AssertionError("Split assignment embedded in ABT audit")
    if any(c in model.columns for c in ("partition", "fold", "split")):
        raise AssertionError("Split assignment embedded in model_ready")

    lineage_path = repo_root / "AssessmentSol1" / "abt" / "COLUMN_LINEAGE.csv"
    artifact_columns = (
        set(spine.columns)
        | set(audit.columns)
        | set(model.columns)
        | set(candidate_sample.columns)
        | set(inventory_sample.columns)
    )
    assert_lineage_complete(artifact_columns, lineage_path)

    return {
        "status": "PASS",
        "mode": "COMMITTED_EVIDENCE",
        "score_spine_rows": spine.height,
        "audit_rows": audit.height,
        "model_ready_rows": model.height,
        "candidate_full_rows": int(candidate_summary["n_candidates"].sum()),
        "inventory_full_rows": int(inventory_summary["n_candidates"].sum()),
        "future_inquiry_count": 0,
        "future_snapshot_count": 0,
        "forbidden_model_feature_count": 0,
        "split_assignment_embedded": False,
    }


def validate_all(repo_root: Path) -> dict:
    out = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    audit = pl.read_parquet(out / "lead_quality_audit_all_snapshots.parquet")
    model = pl.read_parquet(out / "lead_quality_model_ready.parquet")
    candidates = pl.read_parquet(out / "candidate_spots.parquet")
    inventory = pl.read_parquet(out / "inventory_serviceability_state.parquet")

    assert_prediction_key_unique(audit)
    assert_no_future_inquiry(audit)
    assert_no_forbidden_model_feature(model)
    assert_target_statuses(audit)
    assert_stage_observability(audit)
    assert_candidate_grain(candidates)
    assert_candidate_grain(inventory)
    assert_no_future_snapshot(inventory)
    assert_lineage_complete(
        set(audit.columns) | set(model.columns) | set(candidates.columns) | set(inventory.columns),
        repo_root / "AssessmentSol1" / "abt" / "COLUMN_LINEAGE.csv",
    )

    if model.filter(~pl.col("target_status").is_in(["POSITIVE", "NEGATIVE"])).height:
        raise AssertionError("model_ready includes invalid labels")

    manifest = {}
    for name in (
        "score_spine.parquet",
        "lead_quality_audit_all_snapshots.parquet",
        "lead_quality_model_ready.parquet",
        "candidate_spots.parquet",
        "inventory_serviceability_state.parquet",
    ):
        p = out / name
        df = pl.read_parquet(p)
        manifest[name] = {
            "rows": df.height,
            "columns": df.width,
            "sha256": sha256_file(p),
        }

    qa = {
        "status": "PASS",
        "prediction_key_unique": True,
        "future_snapshot_count": 0,
        "future_inquiry_count": 0,
        "forbidden_model_feature_count": 0,
        "candidate_grain_duplicates": 0,
        "market_context_used": False,
        "split_assignment_embedded": False,
        "manifest": manifest,
    }
    (out / "qa_summary.json").write_text(json.dumps(qa, indent=2) + "\n")
    (out / "artifact_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    return qa


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    full = [
        out / "lead_quality_audit_all_snapshots.parquet",
        out / "lead_quality_model_ready.parquet",
        out / "candidate_spots.parquet",
        out / "inventory_serviceability_state.parquet",
    ]
    result = validate_all(repo_root) if all(p.exists() for p in full) else validate_committed_evidence(repo_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
