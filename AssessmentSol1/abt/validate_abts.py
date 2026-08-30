from __future__ import annotations

import hashlib
import json
from pathlib import Path
import polars as pl

from _common import (
    CURRENT_INQUIRY_FEATURES,
    FORBIDDEN_RAW_FEATURES,
    HISTORY_FEATURES,
    UNVERSIONED_SPOT_FIELDS,
    ensure_output_dir,
    load_inquiries,
    load_leads,
)
from build_t0 import build_t0
from build_t1 import build_t1
from build_t2 import build_t2
from build_inventory_candidates import build_inventory_candidates

VALID_TARGET_STATUSES = {"POSITIVE", "NEGATIVE", "AMBIGUOUS", "CENSORED", "INELIGIBLE"}
SPLIT_COLUMNS = {"split", "partition", "fold"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _assert_unique(df: pl.DataFrame, columns: list[str], name: str) -> None:
    if df.group_by(columns).len().filter(pl.col("len") > 1).height:
        raise AssertionError(f"{name}: duplicate grain {columns}")


def _assert_target_contract(audit: pl.DataFrame, model: pl.DataFrame, name: str) -> None:
    statuses = set(audit["target_status"].drop_nulls().to_list())
    invalid = statuses - VALID_TARGET_STATUSES
    if invalid:
        raise AssertionError(f"{name}: invalid target statuses: {sorted(invalid)}")
    if model.filter(~pl.col("target_status").is_in(["POSITIVE", "NEGATIVE"])).height:
        raise AssertionError(f"{name}: model_ready contains non-binary/non-mature labels")
    nonbinary = model.filter(~pl.col("target_value").is_in([0, 1])).height
    if nonbinary:
        raise AssertionError(f"{name}: model_ready target_value is not binary")


def _assert_no_forbidden(df: pl.DataFrame, name: str) -> None:
    forbidden = FORBIDDEN_RAW_FEATURES | UNVERSIONED_SPOT_FIELDS
    overlap = sorted(set(df.columns).intersection(forbidden))
    if overlap:
        raise AssertionError(f"{name}: forbidden fields present: {overlap}")
    market = [c for c in df.columns if c.startswith("market_")]
    if market:
        raise AssertionError(f"{name}: Market Context entered modeling path: {market}")


def _assert_stage_observability(
    t0_model: pl.DataFrame,
    t1_model: pl.DataFrame,
    t2_audit: pl.DataFrame,
    t2_model: pl.DataFrame,
) -> None:
    if set(CURRENT_INQUIRY_FEATURES).intersection(t0_model.columns):
        raise AssertionError("T0 contains inquiry payload")
    if set(HISTORY_FEATURES).intersection(t0_model.columns):
        raise AssertionError("T0 contains inquiry history")
    if set(HISTORY_FEATURES).intersection(t1_model.columns):
        raise AssertionError("T1 contains history despite being first inquiry")
    for name, df in (("T0", t0_model), ("T1", t1_model), ("T2", t2_model)):
        leaked_context = [
            c
            for c in df.columns
            if c.startswith("matching_")
            or c.startswith("inventory_")
            or c in {
                "availability_known",
                "is_available_asof",
                "days_until_available_asof",
                "snapshot_age_days",
                "freshness_bucket",
                "availability_state",
            }
        ]
        if leaked_context:
            raise AssertionError(f"{name} LeadQuality model contains Matching/Inventory: {leaked_context}")
    if t2_audit["audit_response_history_feature_used"].any():
        raise AssertionError("T2 response history was enabled as a predictive feature")
    allowed_stage = {
        "ELIGIBLE",
        "INELIGIBLE_PRIOR_SCHEDULED_VISIT_KNOWN",
        "AMBIGUOUS_PRIOR_SCHEDULED_VISIT_TIME",
    }
    invalid_stage = set(t2_audit["stage_eligibility"].to_list()) - allowed_stage
    if invalid_stage:
        raise AssertionError(f"T2 invalid stage_eligibility values: {sorted(invalid_stage)}")
    if t2_audit.filter(
        pl.col("hist_max_inquiry_time").is_not_null()
        & (pl.col("hist_max_inquiry_time") >= pl.col("score_time"))
    ).height:
        raise AssertionError("T2 includes same-time/future inquiry history")


def _assert_inventory(inventory_audit: pl.DataFrame, inventory_model: pl.DataFrame) -> None:
    _assert_unique(inventory_audit, ["score_id", "candidate_spot_id"], "inventory_candidates")
    if inventory_audit.filter(pl.col("spot_created_at") > pl.col("score_time")).height:
        raise AssertionError("Future Spot exists in candidate universe")
    if inventory_audit.filter(
        pl.col("snapshot_date_asof").is_not_null()
        & (pl.col("snapshot_date_asof") > pl.col("score_time").dt.date())
    ).height:
        raise AssertionError("Future Availability snapshot selected")

    missing = inventory_audit.filter(~pl.col("availability_known"))
    if missing.filter(pl.col("is_available_asof").is_not_null()).height:
        raise AssertionError("Missing snapshot was coerced into available/unavailable")
    if missing.filter(pl.col("days_until_available_asof").is_not_null()).height:
        raise AssertionError("Missing snapshot received days_until_available")
    if missing.filter(pl.col("freshness_bucket") != "UNKNOWN").height:
        raise AssertionError("Missing snapshot freshness must be UNKNOWN")
    if missing.filter(pl.col("availability_state") != "UNKNOWN").height:
        raise AssertionError("Missing snapshot availability_state must be UNKNOWN")
    if "competing_inquiries_30d" in inventory_audit.columns or "competing_inquiries_30d" in inventory_model.columns:
        raise AssertionError("competing_inquiries_30d entered P4 before semantic proof")
    _assert_no_forbidden(inventory_model, "inventory_candidates_model_ready")


def _load_lineage(repo_root: Path) -> pl.DataFrame:
    path = repo_root / "AssessmentSol1" / "abt" / "COLUMN_LINEAGE.csv"
    lineage = pl.read_csv(path)
    required = {
        "column",
        "source",
        "meaning",
        "available_at",
        "transform",
        "role",
        "stage",
        "future_risk",
        "justification",
        "evidence",
    }
    missing = required - set(lineage.columns)
    if missing:
        raise AssertionError(f"COLUMN_LINEAGE missing required fields: {sorted(missing)}")
    if lineage["column"].is_duplicated().any():
        dupes = lineage.filter(pl.col("column").is_duplicated())["column"].unique().to_list()
        raise AssertionError(f"COLUMN_LINEAGE column names must be unique: {dupes}")
    return lineage


def _assert_lineage_gate(
    repo_root: Path,
    outputs: dict[str, pl.DataFrame],
) -> dict[str, list[str]]:
    lineage = _load_lineage(repo_root)
    known = set(lineage["column"].to_list())
    all_columns = set().union(*(set(df.columns) for df in outputs.values()))
    missing = sorted(all_columns - known)
    if missing:
        raise AssertionError(f"Columns without temporal lineage: {missing}")

    lineage_rows = {r["column"]: r for r in lineage.to_dicts()}
    feature_sets: dict[str, list[str]] = {}

    for object_name in ("abt_t0_model_ready", "abt_t1_model_ready", "abt_t2_model_ready"):
        df = outputs[object_name]
        invalid_roles = []
        model_features = []
        for c in df.columns:
            row = lineage_rows[c]
            if row["role"] == "model_feature":
                model_features.append(c)
                if not row["available_at"] or str(row["available_at"]).upper().startswith("UNKNOWN"):
                    raise AssertionError(f"{object_name}.{c}: model feature lacks temporal availability proof")
            elif row["role"] in {"matching_feature", "inventory_feature", "audit_only", "forbidden"}:
                invalid_roles.append((c, row["role"]))
        if invalid_roles:
            raise AssertionError(f"{object_name}: non-LeadQuality roles entered model view: {invalid_roles}")
        feature_sets[object_name] = sorted(model_features)

    inv_features = []
    for c in outputs["inventory_candidates_model_ready"].columns:
        row = lineage_rows[c]
        if row["role"] == "forbidden":
            raise AssertionError(f"inventory_candidates_model_ready.{c}: forbidden by lineage")
        if row["role"] in {"matching_feature", "inventory_feature"}:
            inv_features.append(c)
            if not row["available_at"] or str(row["available_at"]).upper().startswith("UNKNOWN"):
                raise AssertionError(f"inventory_candidates_model_ready.{c}: temporal availability unproven")
    feature_sets["inventory_candidates_model_ready"] = sorted(inv_features)
    return feature_sets


def _assert_split_integrity(repo_root: Path, outputs: dict[str, pl.DataFrame]) -> str:
    for name, df in outputs.items():
        embedded = SPLIT_COLUMNS.intersection(df.columns)
        if embedded:
            raise AssertionError(f"{name}: split/fold assignment embedded in ABT: {sorted(embedded)}")

    split_dir = repo_root / "AssessmentSol1" / "splits"
    candidates = [
        split_dir / "split_assignments.parquet",
        split_dir / "split_assignments.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return "EXTERNAL_SPLIT_NOT_YET_MATERIALIZED"
    split = pl.read_parquet(path) if path.suffix == ".parquet" else pl.read_csv(path)
    partition_col = next((c for c in ("split", "partition", "fold") if c in split.columns), None)
    if "lead_id" not in split.columns or partition_col is None:
        raise AssertionError("Split assignment must contain lead_id and split/partition/fold")
    leakage = split.group_by("lead_id").agg(pl.col(partition_col).n_unique().alias("n")).filter(pl.col("n") > 1)
    if leakage.height:
        raise AssertionError("Split integrity failed: same lead appears in multiple partitions/folds")
    return "PASS"


def validate_all(repo_root: Path, materialize: bool = True) -> dict:
    leads = load_leads(repo_root)
    iq = load_inquiries(repo_root)

    t0_audit, t0_model = build_t0(repo_root)
    t1_audit, t1_model = build_t1(repo_root)
    t2_audit, t2_model = build_t2(repo_root)
    inv_audit, inv_model = build_inventory_candidates(repo_root)

    _assert_unique(t0_audit, ["lead_id"], "abt_t0")
    _assert_unique(t1_audit, ["lead_id"], "abt_t1")
    _assert_unique(t1_audit, ["first_inquiry_id"], "abt_t1")
    _assert_unique(t2_audit, ["inquiry_id"], "abt_t2")

    expected_t1 = iq.filter(pl.col("inquiry_number") == 1).height
    expected_t2 = iq.filter(pl.col("inquiry_number") >= 2).height
    if t0_audit.height != leads.height:
        raise AssertionError("T0 row explosion/loss relative to leads")
    if t1_audit.height != expected_t1:
        raise AssertionError("T1 row explosion/loss relative to deterministic first inquiries")
    if t2_audit.height != expected_t2:
        raise AssertionError("T2 row explosion/loss relative to second+ inquiries")

    for name, audit, model in (
        ("abt_t0", t0_audit, t0_model),
        ("abt_t1", t1_audit, t1_model),
        ("abt_t2", t2_audit, t2_model),
    ):
        _assert_target_contract(audit, model, name)
        _assert_no_forbidden(model, f"{name}_model_ready")

    _assert_stage_observability(t0_model, t1_model, t2_audit, t2_model)
    _assert_inventory(inv_audit, inv_model)

    outputs = {
        "abt_t0_audit_all_rows": t0_audit,
        "abt_t0_model_ready": t0_model,
        "abt_t1_audit_all_rows": t1_audit,
        "abt_t1_model_ready": t1_model,
        "abt_t2_audit_all_rows": t2_audit,
        "abt_t2_model_ready": t2_model,
        "inventory_candidates_audit_all_rows": inv_audit,
        "inventory_candidates_model_ready": inv_model,
    }
    feature_sets = _assert_lineage_gate(repo_root, outputs)
    split_status = _assert_split_integrity(repo_root, outputs)

    out = ensure_output_dir(repo_root)
    manifest: dict[str, dict] = {}
    if materialize:
        for name, df in outputs.items():
            path = out / f"{name}.parquet"
            df.write_parquet(path)
            manifest[path.name] = {
                "rows": df.height,
                "columns": df.width,
                "sha256": _sha256(path),
            }

    qa = {
        "status": "PASS",
        "contract": "P4_POINT_IN_TIME_ABTS_V1",
        "raw_inputs_only": True,
        "t0_rows": t0_audit.height,
        "t1_rows": t1_audit.height,
        "t2_rows": t2_audit.height,
        "inventory_candidate_rows": inv_audit.height,
        "future_inquiry_history_rows": 0,
        "future_spot_rows": 0,
        "future_availability_rows": 0,
        "forbidden_model_columns": 0,
        "market_context_used": False,
        "competing_inquiries_30d_used": False,
        "t2_response_history_feature_used": False,
        "t2_stage_response_gate": "TIMED_ONLY_WITH_UNTIMED_AS_AMBIGUOUS",
        "split_integrity": split_status,
        "feature_sets_from_lineage": feature_sets,
        "manifest": manifest,
    }
    if materialize:
        (out / "p4_qa_summary.json").write_text(json.dumps(qa, indent=2) + "\n")
        (out / "p4_artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return qa


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    print(json.dumps(validate_all(repo_root, materialize=True), indent=2))


if __name__ == "__main__":
    main()
