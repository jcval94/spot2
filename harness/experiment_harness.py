from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CORE_METRICS = {
    "roc_auc",
    "average_precision",
    "brier",
    "log_loss",
    "lift_top_10pct",
    "recall_top_20pct",
}
VALID_CONCLUSIONS = {"SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE"}
VALID_LEAKAGE_STATUSES = {"ALLOW", "BLOCK", "CONDITIONAL", "UNKNOWN"}
EXPERIMENT_ID_RE = re.compile(r"^E\d{3}_[a-z0-9][a-z0-9_-]*$")


class HarnessError(ValueError):
    """Raised when an experiment violates the harness contract."""


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        obj = json.load(fh)
    if not isinstance(obj, dict):
        raise HarnessError(f"{path}: expected a JSON object")
    return obj


def _require_str(obj: dict[str, Any], key: str, context: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HarnessError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _require_list(obj: dict[str, Any], key: str, context: str) -> list[Any]:
    value = obj.get(key)
    if not isinstance(value, list):
        raise HarnessError(f"{context}.{key} must be a list")
    return value


def _validate_str_list(values: list[Any], context: str) -> list[str]:
    if any(not isinstance(v, str) or not v.strip() for v in values):
        raise HarnessError(f"{context} must contain only non-empty strings")
    return [v.strip() for v in values]


def validate_spec(spec: dict[str, Any]) -> None:
    experiment_id = _require_str(spec, "experiment_id", "spec")
    if not EXPERIMENT_ID_RE.fullmatch(experiment_id):
        raise HarnessError(
            "spec.experiment_id must match E###_<short_name> using lowercase letters, digits, _ or -"
        )

    parent = spec.get("parent_experiment")
    if parent is not None:
        if not isinstance(parent, str) or not EXPERIMENT_ID_RE.fullmatch(parent):
            raise HarnessError("spec.parent_experiment must be null or a valid experiment ID")
        if parent == experiment_id:
            raise HarnessError("an experiment cannot be its own parent")

    for key in ("question", "hypothesis", "primary_change"):
        _require_str(spec, key, "spec")

    secondary = spec.get("secondary_changes", [])
    if not isinstance(secondary, list):
        raise HarnessError("spec.secondary_changes must be a list")
    _validate_str_list(secondary, "spec.secondary_changes")

    scoring = spec.get("scoring_time")
    if not isinstance(scoring, dict):
        raise HarnessError("spec.scoring_time must be an object")
    _require_str(scoring, "stage", "spec.scoring_time")
    _require_str(scoring, "timestamp_definition", "spec.scoring_time")

    target = spec.get("target")
    if not isinstance(target, dict):
        raise HarnessError("spec.target must be an object")
    _require_str(target, "event", "spec.target")
    horizon = target.get("horizon_days")
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon <= 0:
        raise HarnessError("spec.target.horizon_days must be a positive integer")
    _require_str(target, "anchor", "spec.target")
    _require_str(target, "censoring", "spec.target")

    population = spec.get("population")
    if not isinstance(population, dict):
        raise HarnessError("spec.population must be an object")
    _require_str(population, "eligibility", "spec.population")
    exclusions = _require_list(population, "exclusions", "spec.population")
    _validate_str_list(exclusions, "spec.population.exclusions")
    period = population.get("period")
    if not isinstance(period, dict) or "start" not in period or "end" not in period:
        raise HarnessError("spec.population.period must contain start and end")

    data_sources = _validate_str_list(
        _require_list(spec, "data_sources", "spec"), "spec.data_sources"
    )
    if not data_sources:
        raise HarnessError("spec.data_sources cannot be empty")

    features = spec.get("features")
    if not isinstance(features, dict):
        raise HarnessError("spec.features must be an object")
    inherited = _validate_str_list(
        _require_list(features, "inherited", "spec.features"), "spec.features.inherited"
    )
    added = _validate_str_list(
        _require_list(features, "added", "spec.features"), "spec.features.added"
    )
    removed = _validate_str_list(
        _require_list(features, "removed", "spec.features"), "spec.features.removed"
    )
    if parent is None and inherited:
        raise HarnessError("a baseline experiment cannot declare inherited features")
    overlaps = (set(inherited) & set(added)) | (set(added) & set(removed)) | (
        set(inherited) & set(removed)
    )
    if overlaps:
        raise HarnessError(f"feature lists overlap: {sorted(overlaps)}")

    validation = spec.get("validation")
    if not isinstance(validation, dict):
        raise HarnessError("spec.validation must be an object")
    _require_str(validation, "strategy", "spec.validation")
    _require_str(validation, "time_column", "spec.validation")
    _require_str(validation, "split_description", "spec.validation")

    metrics = set(
        _validate_str_list(_require_list(spec, "metrics", "spec"), "spec.metrics")
    )
    missing_metrics = CORE_METRICS - metrics
    if missing_metrics:
        raise HarnessError(f"spec.metrics missing core metrics: {sorted(missing_metrics)}")

    _validate_str_list(_require_list(spec, "segments", "spec"), "spec.segments")

    leakage = spec.get("leakage")
    if not isinstance(leakage, dict):
        raise HarnessError("spec.leakage must be an object")
    if leakage.get("check_status") != "PASS":
        raise HarnessError("spec.leakage.check_status must be PASS before execution")

    items = _require_list(leakage, "items", "spec.leakage")
    reviewed_elements: set[str] = set()
    for i, item in enumerate(items):
        context = f"spec.leakage.items[{i}]"
        if not isinstance(item, dict):
            raise HarnessError(f"{context} must be an object")
        element = _require_str(item, "element", context)
        _require_str(item, "source", context)
        _require_str(item, "scoring_time", context)
        _require_str(item, "information_available_at", context)
        _require_str(item, "evidence", context)
        status = item.get("status")
        if status not in VALID_LEAKAGE_STATUSES:
            raise HarnessError(
                f"{context}.status must be one of {sorted(VALID_LEAKAGE_STATUSES)}"
            )
        if status in {"BLOCK", "UNKNOWN"}:
            raise HarnessError(f"{element}: leakage status {status} cannot pass")
        if status == "CONDITIONAL" and item.get("condition_satisfied") is not True:
            raise HarnessError(
                f"{element}: CONDITIONAL leakage item requires condition_satisfied=true"
            )
        reviewed_elements.add(element)

    unreviewed_added = set(added) - reviewed_elements
    if unreviewed_added:
        raise HarnessError(
            f"added features missing leakage review: {sorted(unreviewed_added)}"
        )


def compare_with_parent(
    spec: dict[str, Any], parent_spec: dict[str, Any] | None
) -> dict[str, Any]:
    if parent_spec is None:
        return {"status": "BASELINE", "reasons": []}

    expected_parent = spec.get("parent_experiment")
    actual_parent = parent_spec.get("experiment_id")
    if expected_parent != actual_parent:
        raise HarnessError(
            f"parent mismatch: spec declares {expected_parent!r}, provided parent is {actual_parent!r}"
        )

    comparable_fields = (
        "scoring_time",
        "target",
        "population",
        "data_sources",
        "validation",
    )
    reasons = [
        f"{field} differs from parent"
        for field in comparable_fields
        if spec.get(field) != parent_spec.get(field)
    ]
    return {
        "status": "EQUIVALENT" if not reasons else "NON_EQUIVALENT",
        "reasons": reasons,
    }


def fingerprint_sources(
    spec: dict[str, Any], repo_root: str | Path = "."
) -> list[dict[str, str]]:
    root = Path(repo_root).resolve()
    fingerprints: list[dict[str, str]] = []
    for source in spec["data_sources"]:
        path = (root / source).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise HarnessError(f"data source escapes repo root: {source}") from exc
        if not path.is_file():
            raise HarnessError(f"data source not found: {source}")
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(block)
        fingerprints.append({"path": source, "sha256": digest.hexdigest()})
    return fingerprints


def current_git_sha(repo_root: str | Path = ".") -> str | None:
    env_sha = os.getenv("GITHUB_SHA")
    if env_sha:
        return env_sha
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def validate_results(results: dict[str, Any], spec: dict[str, Any]) -> None:
    if results.get("experiment_id") != spec["experiment_id"]:
        raise HarnessError("results.experiment_id does not match spec.experiment_id")

    metrics = results.get("metrics")
    if not isinstance(metrics, dict):
        raise HarnessError("results.metrics must be an object")
    missing = CORE_METRICS - set(metrics)
    if missing:
        raise HarnessError(f"results.metrics missing core metrics: {sorted(missing)}")
    for metric in CORE_METRICS:
        value = metrics[metric]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise HarnessError(f"results.metrics.{metric} must be numeric")

    conclusion = results.get("conclusion")
    if conclusion not in VALID_CONCLUSIONS:
        raise HarnessError(
            f"results.conclusion must be one of {sorted(VALID_CONCLUSIONS)}"
        )

    caveats = results.get("caveats")
    if not isinstance(caveats, list):
        raise HarnessError("results.caveats must be a list")
    _validate_str_list(caveats, "results.caveats")

    next_experiment = results.get("next_experiment")
    if next_experiment is not None and (
        not isinstance(next_experiment, str) or not next_experiment.strip()
    ):
        raise HarnessError("results.next_experiment must be null or a non-empty string")

    segment_metrics = results.get("segment_metrics", {})
    if not isinstance(segment_metrics, (dict, list)):
        raise HarnessError("results.segment_metrics must be an object or list")


def metric_deltas(
    results: dict[str, Any], parent_results: dict[str, Any] | None
) -> dict[str, float] | None:
    if parent_results is None:
        return None
    parent_metrics = parent_results.get("metrics")
    if not isinstance(parent_metrics, dict):
        raise HarnessError("parent results.metrics must be an object")
    missing = CORE_METRICS - set(parent_metrics)
    if missing:
        raise HarnessError(f"parent results missing core metrics: {sorted(missing)}")
    return {
        metric: float(results["metrics"][metric]) - float(parent_metrics[metric])
        for metric in sorted(CORE_METRICS)
    }


def build_record(
    spec: dict[str, Any],
    results: dict[str, Any],
    *,
    parent_spec: dict[str, Any] | None = None,
    parent_results: dict[str, Any] | None = None,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    validate_spec(spec)
    validate_results(results, spec)
    comparison = compare_with_parent(spec, parent_spec)

    spec_bytes = json.dumps(
        spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    return {
        "schema_version": 1,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": current_git_sha(repo_root),
        "experiment_id": spec["experiment_id"],
        "parent_experiment": spec.get("parent_experiment"),
        "primary_change": spec["primary_change"],
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "data_fingerprints": fingerprint_sources(spec, repo_root),
        "leakage_check": spec["leakage"]["check_status"],
        "comparison": comparison,
        "metrics": results["metrics"],
        "metric_deltas_vs_parent": metric_deltas(results, parent_results),
        "segment_metrics": results.get("segment_metrics", {}),
        "conclusion": results["conclusion"],
        "caveats": results["caveats"],
        "next_experiment": results.get("next_experiment"),
        "spec": spec,
    }


def render_summary(record: dict[str, Any]) -> str:
    lines = [
        f"# {record['experiment_id']}",
        "",
        f"- Parent: {record['parent_experiment'] or 'none'}",
        f"- Primary change: {record['primary_change']}",
        f"- Leakage: {record['leakage_check']}",
        f"- Comparison: {record['comparison']['status']}",
    ]
    for reason in record["comparison"]["reasons"]:
        lines.append(f"  - {reason}")

    lines.extend(["", "## Metrics", "", "| Metric | Value |", "|---|---:|"])
    for metric in sorted(CORE_METRICS):
        lines.append(f"| {metric} | {record['metrics'][metric]:.6g} |")

    deltas = record.get("metric_deltas_vs_parent")
    if deltas:
        lines.extend(["", "## Delta vs parent", "", "| Metric | Delta |", "|---|---:|"])
        for metric in sorted(CORE_METRICS):
            lines.append(f"| {metric} | {deltas[metric]:+.6g} |")

    lines.extend(["", "## Conclusion", "", record["conclusion"], "", "## Caveats", ""])
    if record["caveats"]:
        lines.extend(f"- {item}" for item in record["caveats"])
    else:
        lines.append("- None recorded.")

    lines.extend(["", "## Next experiment", "", record["next_experiment"] or "None."])
    return "\n".join(lines) + "\n"


def write_record(record: dict[str, Any], output_dir: str | Path) -> Path:
    destination = Path(output_dir) / record["experiment_id"]
    record_path = destination / "record.json"
    summary_path = destination / "summary.md"
    if record_path.exists() or summary_path.exists():
        raise HarnessError(
            f"refusing to overwrite finalized experiment record: {destination}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    record_path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    summary_path.write_text(render_summary(record), encoding="utf-8")
    return destination


def _cmd_validate(args: argparse.Namespace) -> int:
    spec = load_json(args.spec)
    validate_spec(spec)
    parent_spec = load_json(args.parent_spec) if args.parent_spec else None
    if parent_spec is not None:
        validate_spec(parent_spec)
    payload = {
        "experiment_id": spec["experiment_id"],
        "leakage_check": spec["leakage"]["check_status"],
        "comparison": compare_with_parent(spec, parent_spec),
        "data_fingerprints": fingerprint_sources(spec, args.repo_root),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _cmd_finalize(args: argparse.Namespace) -> int:
    spec = load_json(args.spec)
    results = load_json(args.results)
    parent_spec = load_json(args.parent_spec) if args.parent_spec else None
    parent_results = load_json(args.parent_results) if args.parent_results else None

    if (parent_spec is None) != (parent_results is None):
        raise HarnessError(
            "--parent-spec and --parent-results must be provided together when finalizing"
        )

    record = build_record(
        spec,
        results,
        parent_spec=parent_spec,
        parent_results=parent_results,
        repo_root=args.repo_root,
    )
    destination = write_record(record, args.output_dir)
    print(destination)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and record traceable Spot2 experiment contracts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate an experiment specification.")
    validate.add_argument("--spec", required=True)
    validate.add_argument("--parent-spec")
    validate.add_argument("--repo-root", default=".")
    validate.set_defaults(func=_cmd_validate)

    finalize = sub.add_parser(
        "finalize", help="Create an immutable experiment record from spec + results."
    )
    finalize.add_argument("--spec", required=True)
    finalize.add_argument("--results", required=True)
    finalize.add_argument("--parent-spec")
    finalize.add_argument("--parent-results")
    finalize.add_argument("--repo-root", default=".")
    finalize.add_argument("--output-dir", default="artifacts/experiment_harness")
    finalize.set_defaults(func=_cmd_finalize)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except HarnessError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
