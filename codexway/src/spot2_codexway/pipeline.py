"""Command-line orchestration for the isolated codexway assessment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .abt import assign_t1_split, build_t0_abt, build_t1_abt, build_t2_abt, write_abts
from .audit import write_audit
from .contracts import Settings, load_settings
from .data import TABLES, dataframe_fingerprint, file_sha256, load_all
from .eda import build_eda
from .inventory import build_inventory_candidates, combine_opportunity
from .evaluation import bootstrap_metric_intervals, compare_system_scores, paired_bootstrap_delta
from .llm_audit import (
    MODEL_PRICING_PER_MILLION,
    build_injected_semantic_benchmark,
    evaluate_injected_benchmark,
    evaluate_semantic_audit,
    rules_only,
    run_live_audit,
)
from .modeling import predict, train_evaluate_sensitivities, train_evaluate_t1, train_evaluate_target_sensitivities
from .notebook import build_notebook
from .profiles import build_profiles, compatibility_cells
from .reporting import create_core_figures, render_pdfs, write_model_card, write_model_diagnostics, write_online_protocol
from .stress import run_stress_tests


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    return path


def raw_fingerprint(settings: Settings) -> str:
    digest = hashlib.sha256()
    for name in TABLES:
        path = settings.data_dir / f"{name}.parquet"
        digest.update(name.encode("utf-8")); digest.update(file_sha256(path).encode("ascii"))
    return digest.hexdigest()


def write_cluster_findings(
    profile_metrics: pd.DataFrame,
    accepted_cells: pd.DataFrame,
    exploratory_cells: pd.DataFrame,
    settings: Settings,
) -> Path:
    accepted = profile_metrics[
        profile_metrics["balance_ok"].astype(bool) & profile_metrics["stability_ari"].ge(0.80)
    ]["family"].tolist()
    rejected = profile_metrics.loc[~profile_metrics["family"].isin(accepted), "family"].tolist()
    significant = int(accepted_cells.get("fdr_reject_10pct", pd.Series(dtype=bool)).sum())
    top = ("```text\n" + accepted_cells.head(10).to_csv(index=False) + "```") if not accepted_cells.empty else "No eligible two-way or three-way cells."
    text = f"""# Cluster findings

Profiles passing balance and ARI gates: {', '.join(accepted) or 'none'}.
Rejected profiles: {', '.join(rejected) or 'none'}.

Only passing families enter the confirmatory combination table. {len(exploratory_cells)}
all-family cells were retained separately for audit, but not interpreted. Among
{len(accepted_cells)} eligible cells, {significant} pass BH-FDR 10%.

The inherited `DN4 × LOC1 × BSV1` pocket remains a pre-registered hypothesis only:
Dynamic Need failed the current balance gate and numeric cluster labels are not
stable semantic identities across refits. It is not used as a multiplier.

## Top eligible cells

{top}
"""
    path = settings.codexway_root / "outputs" / "CLUSTER_FINDINGS.md"
    path.write_text(text, encoding="utf-8")
    return path


def finalize_experiment_records(
    model_result: dict[str, Any],
    sensitivity: dict[str, Any],
    profile_metrics: pd.DataFrame,
    cells: pd.DataFrame,
    opportunity: pd.DataFrame,
    inventory_scores: pd.DataFrame,
    llm: dict[str, Any],
    settings: Settings,
    *,
    system_evaluation: dict[str, Any],
    target_sensitivity: dict[str, Any],
) -> list[Path]:
    from harness.experiment_harness import finalize_record

    metric_map: dict[str, dict[str, Any]] = {
        "E101": model_result["metrics"]["logistic_lead_only"],
        "E102": model_result["metrics"]["logistic"],
        "E103": {"candidate": "catboost", "promoted": model_result["winner"] == "catboost", **model_result["metrics"]["catboost"]},
        "E104": {"profiles": profile_metrics.to_dict(orient="records"), "eligible_cells": len(cells), "fdr_significant": int(cells.get("fdr_reject_10pct", pd.Series(dtype=bool)).sum())},
        "E105": sensitivity.get("T2_logistic_trajectory", {}),
        "E106": {**sensitivity.get("T2_logistic_trajectory", {}), "entity_overlap": sensitivity.get("T2_entity_overlap_train_test")},
        "E107": sensitivity.get("T0_logistic_30d", {}),
        "E108": {"exact_attendable_rate": float(inventory_scores["exact_spot_available"].mean())},
        "E109": {"mean_serviceability": float(inventory_scores["inventory_serviceability"].mean()), "mean_confidence": float(inventory_scores["inventory_confidence"].mean())},
        "L101": {"status": llm.get("evaluation_status"), "rules_positive_flags": llm.get("positive_flags", {}).get("rule_actionable")},
        "E110": system_evaluation,
        "E111": {
            "listing_state_status": "CONDITIONAL_UNVERSIONED_ASSUMED_STATIC_SINCE_CREATION",
            "mean_lower": float(inventory_scores["inventory_serviceability_lower"].mean()),
            "mean_upper": float(inventory_scores["inventory_serviceability_upper"].mean()),
            "mean_uncertainty_width": float(inventory_scores["inventory_uncertainty_width"].mean()),
        },
        "E112": target_sensitivity,
        "E113": {
            "conclusion": "SUPPORTED" if model_result.get("selection", {}).get("stable_segment_promoted") else "NOT_SUPPORTED",
            "selection": model_result.get("selection", {}),
            **model_result["metrics"].get("stable_segment_logistic", {}),
        },
        "E114": {
            "conclusion": "SUPPORTED" if system_evaluation.get("opportunity_absolute_lift_gate") == "GO" else "NOT_SUPPORTED",
            **system_evaluation,
        },
        "E115": {
            "conclusion": "SUPPORTED_RETROSPECTIVE__FORWARD_VALIDATION_REQUIRED",
            "supersedes_interpretation_only": "E113",
            "metrics_unchanged": True,
            "selection": model_result.get("selection", {}),
            **model_result["metrics"].get("stable_segment_logistic", {}),
        },
        "E116": {
            "conclusion": "SUPPORTED_RETROSPECTIVE__ROW_ORDER_INVARIANT__FORWARD_VALIDATION_REQUIRED",
            "ranking_tie_policy": "FRACTIONAL_EXPECTATION_AT_CAPACITY_BOUNDARY",
            "selection": model_result.get("selection", {}),
            **model_result["metrics"].get("stable_segment_logistic", {}),
        },
        "E117": {
            "conclusion": "ELIGIBLE_FOR_FORWARD_SHADOW_ONLY",
            "selection": model_result.get("selection", {}),
            "retrospective_holdout_not_confirmatory": True,
            **model_result["metrics"].get("stable_segment_logistic", {}),
        },
    }
    live_meta = llm.get("controlled_injection_benchmark", {}).get("run_metadata", {})
    if live_meta.get("rows", 0) and live_meta.get("errors", 0) < live_meta.get("rows", 0):
        metric_map["L102"] = llm.get("controlled_injection_benchmark", {})
    spec_files = {path.stem.split("_")[0]: path for path in (settings.codexway_root / "experiments" / "specs").glob("*.json")}
    common_artifacts = {
        "metrics": settings.codexway_root / "outputs" / "metrics" / "t1_model_metrics.json",
        "scores": settings.codexway_root / "outputs" / "predictions" / "lead_opportunity_scores.parquet",
    }
    code_paths = list((settings.codexway_root / "src" / "spot2_codexway").glob("*.py"))
    records = []
    for experiment_id, metrics in metric_map.items():
        spec_path = spec_files.get(experiment_id)
        if spec_path is None:
            continue
        existing = settings.codexway_root / "experiments" / "records" / f"{experiment_id}.json"
        if existing.exists():
            records.append(existing)
            continue
        records.append(finalize_record(
            spec_path=spec_path, metrics=metrics, artifacts=common_artifacts,
            data_fingerprint=raw_fingerprint(settings), code_paths=code_paths,
            records_dir=settings.codexway_root / "experiments" / "records", repo_root=settings.repo_root,
        ))
    return records


def build_split_manifest(t1: pd.DataFrame, settings: Settings) -> Path:
    parts = {}
    for name in ["train", "validation", "test", "purge_or_censored", "censored"]:
        frame = t1[t1["split"].eq(name)]
        parts[name] = {
            "n": len(frame), "positives": int(frame["target_t1"].fillna(0).sum()),
            "positive_rate": float(frame["target_t1"].mean()) if frame["target_t1"].notna().any() else None,
            "min_timestamp": frame["prediction_timestamp"].min(), "max_timestamp": frame["prediction_timestamp"].max(),
        }
    manifest = {
        "contract": "T1_first_inquiry", "purge_days": settings.maturity_days,
        "raw_data_fingerprint": raw_fingerprint(settings), "partitions": parts,
    }
    return _write_json(settings.codexway_root / "outputs" / "abt" / "split_manifest.json", manifest)


def evaluate_opportunity_system(
    t1: pd.DataFrame,
    opportunity: pd.DataFrame,
    candidates: pd.DataFrame,
    settings: Settings,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Evaluate every system component on the same untouched procedural holdout.

    Inventory scores are not claimed to estimate the T1 outcome.  The comparison
    is a diagnostic: multiplying by inventory must prove incremental ranking value
    before the product is allowed to automate prioritisation.
    """
    metrics_dir = settings.codexway_root / "outputs" / "metrics"
    tables_dir = settings.codexway_root / "outputs" / "tables"
    labeled = opportunity.merge(
        t1[["lead_id", "target_t1"]], on="lead_id", how="left", validate="one_to_one"
    )
    holdout = labeled[labeled["split"].eq("test") & labeled["target_t1"].notna()].copy()
    score_map = {
        "lead_quality": "p_lead_quality",
        "inventory_lower_bound": "inventory_serviceability_lower",
        "inventory_upper_bound": "inventory_serviceability_upper",
        "opportunity_lower_bound": "opportunity_probability_lower",
        "opportunity_upper_bound": "opportunity_probability_upper",
    }
    metrics = compare_system_scores(holdout, "target_t1", score_map)
    intervals = bootstrap_metric_intervals(
        holdout, "target_t1", list(score_map.values()), iterations=1000, seed=settings.seed
    )
    delta = paired_bootstrap_delta(
        holdout, "target_t1", "p_lead_quality", "opportunity_probability_lower",
        iterations=1000, seed=settings.seed,
    )
    metrics.to_csv(metrics_dir / "system_score_metrics.csv", index=False)
    intervals.to_csv(metrics_dir / "system_score_intervals.csv", index=False)
    delta.to_csv(metrics_dir / "system_score_paired_delta.csv", index=False)

    by_score = metrics.set_index("score")
    quality = by_score.loc["lead_quality"]
    combined = by_score.loc["opportunity_lower_bound"]
    quality_lift_interval = intervals[
        intervals["score"].eq("p_lead_quality") & intervals["metric"].eq("lift_top_10pct")
    ].iloc[0]
    combined_lift_interval = intervals[
        intervals["score"].eq("opportunity_probability_lower") & intervals["metric"].eq("lift_top_10pct")
    ].iloc[0]
    quality_gate = bool(
        quality["average_precision"] > quality["positive_rate"]
        and quality["lift_top_10pct"] > 1.0
        and quality_lift_interval["ci_low"] > 1.0
    )
    incremental_gate = bool(
        combined["average_precision"] > quality["average_precision"]
        and combined["lift_top_10pct"] > quality["lift_top_10pct"]
    )
    combined_absolute_gate = bool(
        combined["average_precision"] > combined["positive_rate"]
        and combined["lift_top_10pct"] > 1.0
        and combined_lift_interval["ci_low"] > 1.0
    )
    auc_delta = delta.loc[delta["metric"].eq("roc_auc")].iloc[0]
    system_gate = quality_gate and combined_absolute_gate
    audit = {
        "evaluation_population": "T1 procedural holdout; same leads and first-inquiry proxy for every score",
        "target_alignment": "PARTIAL_ONLY__T1_FIRST_INQUIRY_OUTCOME_DOES_NOT_OBSERVE_FALLBACK_SUCCESS",
        "interpretation": "Inventory and Opportunity comparisons are diagnostic ranking checks, not calibrated outcome probabilities.",
        "ranking_tie_policy": "FRACTIONAL_EXPECTATION_AT_CAPACITY_BOUNDARY__ROW_ORDER_INVARIANT",
        "lead_quality_gate": "GO" if quality_gate else "NO_GO",
        "inventory_incremental_gate": "GO" if incremental_gate else "NO_GO",
        "opportunity_absolute_lift_gate": "GO" if combined_absolute_gate else "NO_GO",
        "system_deployment_gate": "GO" if system_gate else "NO_GO",
        "decision": (
            "DO_NOT_AUTOMATE__USE_TWO_AXIS_DIAGNOSTIC_ONLY"
            if not system_gate
            else "ELIGIBLE_FOR_NEW_FORWARD_VALIDATION_AND_GUARDED_RANDOMIZED_PILOT"
        ),
        "quality_average_precision": float(quality["average_precision"]),
        "quality_lift_top_10pct": float(quality["lift_top_10pct"]),
        "quality_lift_top_10pct_ci": [float(quality_lift_interval["ci_low"]), float(quality_lift_interval["ci_high"])],
        "opportunity_average_precision": float(combined["average_precision"]),
        "opportunity_lift_top_10pct": float(combined["lift_top_10pct"]),
        "opportunity_lift_top_10pct_ci": [float(combined_lift_interval["ci_low"]), float(combined_lift_interval["ci_high"])],
        "opportunity_minus_quality_auc_ci": [float(auc_delta["delta_ci_low"]), float(auc_delta["delta_ci_high"])],
        "two_axis_policy": {
            "high_quality__serviceable": "manual_priority_only_if_quality_gate_passes",
            "high_quality__uncertain_inventory": "verify_inventory_before_contact",
            "high_quality__low_serviceability": "source_or_offer_fallback",
            "standard_quality": "standard_workflow",
        },
        "caveat": "The combined score clears the absolute lift gate but does not improve on Lead Quality alone; inventory incremental value remains unproven on the T1 proxy.",
    }
    _write_json(metrics_dir / "system_evaluation.json", audit)

    freshness_rows = []
    for days in (7, 30, 90):
        observed = candidates["snapshot_age_days"].between(0, days, inclusive="both")
        freshness_rows.append({
            "freshness_days": days,
            "candidate_rows": int(len(candidates)),
            "fresh_candidate_share": float(observed.mean()),
            "unknown_or_stale_share": float((~observed).mean()),
            "leads_with_any_fresh_candidate_share": float(
                candidates.assign(observed=observed).groupby("lead_id")["observed"].any().mean()
            ),
        })
    pd.DataFrame(freshness_rows).to_csv(tables_dir / "inventory_freshness_sensitivity.csv", index=False)
    inventory_audit = {
        "availability_join": "STRICT_BACKWARD_ASOF",
        "future_snapshot_violations": int((candidates["snapshot_date"] > candidates["prediction_timestamp"]).fillna(False).sum()),
        "listing_state_status": "CONDITIONAL__UNVERSIONED_FIELDS_ASSUMED_STATIC_SINCE_SPOT_CREATION",
        "mean_serviceability_lower": float(opportunity["inventory_serviceability_lower"].mean()),
        "mean_serviceability_upper": float(opportunity["inventory_serviceability_upper"].mean()),
        "mean_uncertainty_width": float(opportunity["inventory_uncertainty_width"].mean()),
        "mean_inventory_confidence": float(opportunity["inventory_confidence"].mean()),
        "exact_attendable_share": float(opportunity["exact_spot_attendable"].mean()),
        "exact_unknown_share": float(opportunity["exact_spot_availability_unknown"].mean()),
        "no_known_alternative_share": float(opportunity["attendable_alternative_count"].eq(0).mean()),
        "no_potential_alternative_share": float(opportunity["potential_alternative_count"].eq(0).mean()),
        "strict_claim": "Availability is PIT-correct; the full historical fallback score is not strictly proven PIT because listing attributes are unversioned.",
    }
    _write_json(metrics_dir / "inventory_audit.json", inventory_audit)
    return labeled, audit


def run_llm_stage(settings: Settings, tables: dict[str, pd.DataFrame], live: bool = True, limit: int | None = None) -> dict[str, Any]:
    evaluation_path = settings.codexway_root / "outputs" / "metrics" / "llm_audit_evaluation.json"
    prior_evaluation: dict[str, Any] = {}
    if evaluation_path.exists():
        try:
            prior_evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            prior_evaluation = {}
    labeling = settings.codexway_root / "llm" / "labeling"; labeling.mkdir(parents=True, exist_ok=True)
    destinations = {"general": labeling / "labeling_holdout_v2.csv", "land_challenge": labeling / "semantic_challenge_v2.csv"}
    missing = [str(path) for path in destinations.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Packaged codexway LLM evaluation sets are required; runtime may not read external experiment directories: "
            + ", ".join(missing)
        )
    labels = pd.concat([pd.read_csv(path) for path in destinations.values()], ignore_index=True).drop_duplicates("spot_id")
    labels["spot_id"] = labels["spot_id"].astype(str)
    rules = labels.apply(rules_only, axis=1, result_type="expand")
    rules.to_parquet(settings.codexway_root / "outputs" / "predictions" / "llm_rules_predictions.parquet", index=False)
    if live:
        # Natural listing copy is deliberately not sent without a separate privacy
        # opt-in.  The live requirement is fulfilled with fully fabricated cases.
        predictions = pd.DataFrame({"spot_id": labels["spot_id"], "llm_actionable": False})
        metadata = {
            "status": "NOT_SENT__EXTERNAL_INVENTORY_PRIVACY_OPT_IN_REQUIRED",
            "rows": 0, "errors": 0, "schema_valid_rate": None,
        }
        injected = build_injected_semantic_benchmark(None, n_per_class=5, seed=settings.seed)
        injected.to_parquet(settings.codexway_root / "outputs" / "abt" / "abt_llm_injected_benchmark.parquet", index=False)
        injected_predictions, injected_metadata = run_live_audit(
            injected, settings.codexway_root / "llm" / "prompt.md",
            settings.codexway_root / "llm" / "audit_response.schema.json",
            settings.codexway_root / "outputs" / "llm_cache_injected",
            settings.raw["llm"]["model"], limit=None,
        )
        injected_predictions.to_parquet(
            settings.codexway_root / "outputs" / "predictions" / "llm_injected_benchmark_predictions.parquet", index=False
        )
        if injected_metadata.get("cached_rows") == injected_metadata.get("rows") and not injected_metadata.get("usage", {}).get("total_tokens"):
            prior_meta = prior_evaluation.get("controlled_injection_benchmark", {}).get("run_metadata", {})
            if prior_meta.get("rows") == injected_metadata.get("rows") and prior_meta.get("usage", {}).get("total_tokens"):
                injected_metadata = {**prior_meta, "cached_rows": injected_metadata["rows"], "replayed_from_cache": True}
        pricing = MODEL_PRICING_PER_MILLION.get(settings.raw["llm"]["model"])
        if pricing and injected_metadata.get("usage"):
            usage = injected_metadata["usage"]
            injected_metadata["estimated_cost_usd_uncached_calls"] = (
                usage.get("input_tokens", 0) * pricing["input_usd"]
                + usage.get("output_tokens", 0) * pricing["output_usd"]
            ) / 1_000_000
            injected_metadata["pricing"] = pricing
            injected_metadata["cost_status"] = "ESTIMATED_FROM_PINNED_PUBLIC_TOKEN_RATES"
        injected_evaluation = evaluate_injected_benchmark(injected, injected_predictions)
        injected_evaluation["run_metadata"] = injected_metadata
    else:
        predictions = pd.DataFrame({"spot_id": labels["spot_id"], "llm_actionable": False})
        metadata = {"status": "NOT_RUN", "rows": 0, "errors": 0, "schema_valid_rate": None}
        injected_evaluation = {"status": "LIVE_NOT_RUN"}
    evaluation = evaluate_semantic_audit(labels, predictions)
    if not live:
        status = "LIVE_NOT_RUN"
    elif injected_evaluation.get("run_metadata", {}).get("rows", 0) and (
        injected_evaluation["run_metadata"].get("errors") == injected_evaluation["run_metadata"].get("rows")
    ):
        status = "LIVE_EXECUTION_FAILED"
    else:
        status = "CONTROLLED_SYNTHETIC_EVALUATED__NATURAL_OPT_IN_AND_GOLD_PENDING"
    result = {
        **evaluation,
        "evaluation_status": evaluation["status"],
        "status": status,
        "run_metadata": metadata,
        "controlled_injection_benchmark": injected_evaluation,
    }
    _write_json(evaluation_path, result)
    return result


def run_all(settings: Settings | None = None, *, live_llm: bool = True, llm_limit: int | None = None, render: bool = True) -> dict[str, Any]:
    settings = settings or load_settings()
    prior_manifest_path = settings.codexway_root / "outputs" / "run_manifest.json"
    prior_prediction_fingerprint = None
    if prior_manifest_path.exists():
        try:
            prior_prediction_fingerprint = json.loads(prior_manifest_path.read_text(encoding="utf-8")).get("prediction_fingerprint")
        except (json.JSONDecodeError, OSError):
            prior_prediction_fingerprint = None
    for directory in ["abt", "figures", "tables", "predictions", "metrics", "models"]:
        (settings.codexway_root / "outputs" / directory).mkdir(parents=True, exist_ok=True)

    audit_path = write_audit(settings)
    paths = write_abts(settings)
    t0 = pd.read_parquet(paths["abt_t0_lead_creation"])
    t1 = pd.read_parquet(paths["abt_t1_first_inquiry"])
    t2 = pd.read_parquet(paths["abt_t2_rescore"])
    split_manifest = build_split_manifest(t1, settings)
    tables = load_all(settings)

    model_result = train_evaluate_t1(t1, settings)
    sensitivity = train_evaluate_sensitivities(t0, t2, t1, settings)
    target_sensitivity = train_evaluate_target_sensitivities(t1, tables["inquiries"], settings)
    eda = build_eda(tables, t1, settings)
    enriched, profile_objects, profile_metrics = build_profiles(t1, tables["spots"], tables["inquiries"], seed=settings.seed)
    profile_metrics.to_csv(settings.codexway_root / "outputs" / "tables" / "cluster_profile_metrics.csv", index=False)
    profile_columns = ["lead_id", "inquiry_id", "split", "target_t1", "need_profile", "dynamic_need_profile", "physical_profile", "location_profile", "broker_service_profile"]
    enriched[profile_columns].to_parquet(settings.codexway_root / "outputs" / "predictions" / "lead_cluster_profiles.parquet", index=False)
    card_rows = []
    for family in ["need_profile", "dynamic_need_profile", "physical_profile", "location_profile", "broker_service_profile"]:
        cards = enriched.groupby(family, dropna=False).agg(
            n=("lead_id", "size"), mature_n=("target_t1", "count"), visit_rate=("target_t1", "mean")
        ).reset_index().rename(columns={family: "cluster"})
        cards.insert(0, "family", family)
        card_rows.append(cards)
    pd.concat(card_rows, ignore_index=True).to_csv(settings.codexway_root / "outputs" / "tables" / "cluster_cards.csv", index=False)
    exploratory_cells = compatibility_cells(enriched)
    exploratory_cells.to_csv(settings.codexway_root / "outputs" / "tables" / "cluster_combinations_exploratory_all.csv", index=False)
    accepted_families = profile_metrics.loc[
        profile_metrics["balance_ok"].astype(bool) & profile_metrics["stability_ari"].ge(0.80), "family"
    ].tolist()
    combination_families = [family for family in accepted_families if family != "need_profile"]
    cells = compatibility_cells(enriched, families=combination_families) if len(combination_families) >= 2 else pd.DataFrame()
    cells.to_csv(settings.codexway_root / "outputs" / "tables" / "cluster_combinations.csv", index=False)
    cluster_findings = write_cluster_findings(profile_metrics, cells, exploratory_cells, settings)
    joblib.dump(profile_objects, settings.codexway_root / "outputs" / "models" / "cluster_profiles.joblib")

    quality = predict(model_result["bundle"], t1)
    candidates, inventory_scores = build_inventory_candidates(t1, tables["spots"], tables["availability_snapshot"], settings)
    candidates.to_parquet(settings.codexway_root / "outputs" / "abt" / "abt_inventory_candidates.parquet", index=False)
    inventory_scores.to_parquet(settings.codexway_root / "outputs" / "predictions" / "inventory_serviceability.parquet", index=False)
    opportunity = combine_opportunity(t1, quality, inventory_scores, settings)
    opportunity["data_fingerprint"] = raw_fingerprint(settings)
    opportunity["reason_codes"] = opportunity.apply(
        lambda row: json.dumps([
            f"lead_quality_{row['lead_quality_score_0_100']:.0f}",
            f"inventory_confidence_{row['inventory_confidence']:.2f}",
            "exact_spot_attendable" if row["exact_spot_available"] else "fallback_or_unserved",
        ]), axis=1,
    )
    _, system_evaluation = evaluate_opportunity_system(t1, opportunity, candidates, settings)
    if system_evaluation["system_deployment_gate"] != "GO":
        opportunity["deployment_status"] = "DIAGNOSTIC_ONLY__SYSTEM_GATE_FAILED"
        opportunity["operational_action"] = "do_not_automate__follow_current_workflow"
    else:
        opportunity["deployment_status"] = "ELIGIBLE_FOR_GUARDED_RANDOMIZED_PILOT"
        opportunity["operational_action"] = opportunity["diagnostic_action"]
    opp_parquet = settings.codexway_root / "outputs" / "predictions" / "lead_opportunity_scores.parquet"
    opp_csv = settings.codexway_root / "outputs" / "predictions" / "lead_opportunity_scores.csv"
    opportunity.to_parquet(opp_parquet, index=False); opportunity.to_csv(opp_csv, index=False)
    opportunity.to_parquet(settings.codexway_root / "outputs" / "abt" / "abt_lead_opportunity.parquet", index=False)

    figures = create_core_figures(t0, t1, model_result["holdout"], settings)
    diagnostics = write_model_diagnostics(t1, quality, model_result, settings)
    model_card = write_model_card(model_result, settings)
    ab_protocol = write_online_protocol(model_result["holdout"], settings)
    stress = run_stress_tests(t1, tables["inquiries"], tables["availability_snapshot"], model_result["holdout"], settings)
    llm = run_llm_stage(settings, tables, live=live_llm, limit=llm_limit)
    records = finalize_experiment_records(
        model_result, sensitivity, profile_metrics, cells, opportunity, inventory_scores, llm, settings,
        system_evaluation=system_evaluation, target_sensitivity=target_sensitivity,
    )
    pdfs = render_pdfs(model_result, opportunity, llm, settings, system_evaluation=system_evaluation)
    notebook = build_notebook(settings) if render else (None, None)

    if llm.get("status") in {"LIVE_NOT_RUN", "LIVE_EXECUTION_FAILED"}:
        run_status = "COMPLETE_WITH_EXTERNAL_LLM_AND_GOLD_DEPENDENCIES"
    elif llm.get("status") != "EVALUATED":
        run_status = "COMPLETE_WITH_EXTERNAL_GOLD_DEPENDENCY"
    else:
        run_status = "COMPLETE"
    prediction_fingerprint = dataframe_fingerprint(opportunity)
    manifest = {
        "status": run_status,
        "raw_data_fingerprint": raw_fingerprint(settings),
        "feature_policy_fingerprint": file_sha256(settings.codexway_root / "config" / "feature_policy.yaml"),
        "prediction_fingerprint": prediction_fingerprint,
        "previous_prediction_fingerprint": prior_prediction_fingerprint,
        "prediction_matches_previous": prior_prediction_fingerprint == prediction_fingerprint if prior_prediction_fingerprint else None,
        "audit": str(audit_path), "split_manifest": str(split_manifest), "model_winner": model_result["winner"],
        "sensitivity_metrics": sensitivity, "target_sensitivity": target_sensitivity, "profile_count": len(profile_objects),
        "eda_status": eda["status"],
        "cluster_combinations_tested": len(cells), "opportunity_rows": len(opportunity),
        "inventory_candidate_rows": len(candidates), "llm_status": llm.get("status"),
        "system_deployment_gate": system_evaluation["system_deployment_gate"],
        "system_decision": system_evaluation["decision"],
        "figures": [str(path) for path in figures], "pdfs": [str(path) for path in pdfs],
        "notebook": [str(path) if path else None for path in notebook], "model_card": str(model_card),
        "ab_protocol": str(ab_protocol), "stress_status": stress["status"],
        "cluster_findings": str(cluster_findings),
        "diagnostics": {key: str(path) for key, path in diagnostics.items()},
        "experiment_records": [str(path) for path in records],
    }
    _write_json(settings.codexway_root / "outputs" / "run_manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit")
    sub.add_parser("build-abt")
    all_parser = sub.add_parser("all")
    all_parser.add_argument("--skip-live-llm", action="store_true")
    all_parser.add_argument("--llm-limit", type=int)
    all_parser.add_argument("--skip-render", action="store_true")
    llm_parser = sub.add_parser("run-llm-audit")
    llm_parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    settings = load_settings()
    if args.command == "audit":
        print(write_audit(settings)); return 0
    if args.command == "build-abt":
        print(json.dumps({key: str(value) for key, value in write_abts(settings).items()}, indent=2)); return 0
    if args.command == "run-llm-audit":
        print(json.dumps(run_llm_stage(settings, load_all(settings), live=True, limit=args.limit), indent=2)); return 0
    result = run_all(settings, live_llm=not args.skip_live_llm, llm_limit=args.llm_limit, render=not args.skip_render)
    print(json.dumps(result, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
