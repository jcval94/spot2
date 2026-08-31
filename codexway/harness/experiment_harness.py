"""Small, self-contained experiment contract and immutable record writer."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


FORBIDDEN_FEATURE_TOKENS = {
    "broker_response", "broker_response_hours", "lead_score_internal",
    "days_on_market", "total_views", "total_inquiries", "is_active",
    "competing_inquiries_30d", "market_context", "future_inquiry_count",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataframe_fingerprint(frame: pd.DataFrame) -> str:
    ordered = frame.reindex(sorted(frame.columns), axis=1).sort_values(
        by=sorted(frame.columns), kind="stable", na_position="first"
    )
    values = pd.util.hash_pandas_object(ordered, index=False).values.tobytes()
    return hashlib.sha256(values).hexdigest()


def validate_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"experiment_id", "parent_id", "contract", "feature_names", "change", "deployable"}
    missing = required - set(spec)
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
    if spec.get("deployable") is False:
        errors.append("NON_DEPLOYABLE diagnostic specs cannot be finalized")
    features = {str(name) for name in spec.get("feature_names", [])}
    forbidden = sorted(features & FORBIDDEN_FEATURE_TOKENS)
    if forbidden and spec.get("deployable", True):
        errors.append(f"deployable spec contains forbidden features: {forbidden}")
    if spec.get("contract") == "T1" and spec.get("join_direction") not in {None, "backward"}:
        errors.append("T1 availability join must be backward")
    if spec.get("uses_future_information") and spec.get("deployable", True):
        errors.append("future information cannot be deployable")
    return errors


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    spec_sha256: str
    status: str
    created_at_utc: str
    git_commit: str
    data_fingerprint: str
    code_fingerprint: str
    metrics: dict[str, Any]
    artifacts: dict[str, str]
    environment: dict[str, Any]


def git_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNKNOWN"


def finalize_record(
    spec_path: Path,
    metrics: dict[str, Any],
    artifacts: dict[str, Path],
    data_fingerprint: str,
    code_paths: list[Path],
    records_dir: Path,
    repo_root: Path,
) -> Path:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    errors = validate_spec(spec)
    if errors:
        raise ValueError("; ".join(errors))
    code_hash = hashlib.sha256()
    for path in sorted(code_paths):
        code_hash.update(path.as_posix().encode("utf-8"))
        code_hash.update(path.read_bytes())
    records_dir.mkdir(parents=True, exist_ok=True)
    target = records_dir / f"{spec['experiment_id']}.json"
    if target.exists():
        raise FileExistsError(
            f"Experiment record {target.name} is immutable; create a child experiment instead"
        )
    record = ExperimentRecord(
        experiment_id=spec["experiment_id"],
        spec_sha256=sha256_path(spec_path),
        status="FINALIZED",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        git_commit=git_commit(repo_root),
        data_fingerprint=data_fingerprint,
        code_fingerprint=code_hash.hexdigest(),
        metrics=metrics,
        artifacts={name: str(path) for name, path in artifacts.items()},
        environment={"python": sys.version, "platform": platform.platform()},
    )
    target.write_text(json.dumps(record.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
