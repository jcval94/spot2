"""Cross-sectional semantic inventory audit, isolated from historical scoring."""

from __future__ import annotations

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import jsonschema
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

ACTIONABLE = {"contradiction", "semantic_cross_field_mismatch"}
MODEL_PRICING_PER_MILLION = {
    "gpt-5.6-luna": {
        "input_usd": 0.20,
        "output_usd": 1.20,
        "as_of": "2026-08-30",
        "source": "https://developers.openai.com/api/docs/models/gpt-5.6-luna",
    }
}


def _serializable(value: Any) -> Any:
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def listing_payload(row: pd.Series) -> dict[str, Any]:
    fields = [
        "spot_id", "sector_name", "type_name", "state", "municipality",
        "settlement", "corridor", "region", "title", "description", "area_sqm",
        "modality", "price_sqm_mxn_rent", "price_sqm_mxn_sale", "natural_light",
        "luminaires", "charging_ports", "security_type", "floor_level", "elevators",
        "vertical_height_m", "parking_spaces", "building_status", "floor_material",
        "amenities",
    ]
    return {field: _serializable(row.get(field)) for field in fields}


def rules_only(row: pd.Series) -> dict[str, Any]:
    """High-precision lexical baseline; intentionally conservative."""
    text = f"{row.get('title', '')} {row.get('description', '')}".lower()
    sector = str(row.get("sector_name", "")).lower()
    issues: list[dict[str, Any]] = []
    interior_terms = ["oficina", "corporativo", "piso", "elevador", "recepción", "recepcion"]
    land_terms = ["terreno", "lote", "predio", "hectárea", "hectarea"]
    if sector == "land" and any(term in text for term in interior_terms):
        evidence = next(term for term in interior_terms if term in text)
        issues.append({
            "classification": "semantic_cross_field_mismatch",
            "evidence_text": evidence,
            "structured_field": "sector_name",
            "structured_value": row.get("sector_name"),
            "actionable": True,
        })
    if sector != "land" and any(term in text for term in land_terms) and "bodega" not in text:
        evidence = next(term for term in land_terms if term in text)
        issues.append({
            "classification": "semantic_cross_field_mismatch",
            "evidence_text": evidence,
            "structured_field": "sector_name",
            "structured_value": row.get("sector_name"),
            "actionable": True,
        })
    return {"spot_id": row["spot_id"], "rule_actionable": bool(issues), "rule_issues": issues}


def build_labeling_sets(
    spots: pd.DataFrame,
    attributes: pd.DataFrame,
    general_ids_path: Path,
    challenge_ids_path: Path,
) -> dict[str, pd.DataFrame]:
    """Rebuild text samples from canonical Parquet, avoiding mojibake in legacy CSVs."""
    source = spots.merge(attributes, on="spot_id", how="left", validate="one_to_one")
    source = source.copy()
    source["spot_id"] = source["spot_id"].astype(str)
    outputs: dict[str, pd.DataFrame] = {}
    for name, path in {"general": general_ids_path, "land_challenge": challenge_ids_path}.items():
        ids = pd.read_csv(path, usecols=["spot_id"])["spot_id"].astype(str)
        sample = ids.to_frame().merge(source, on="spot_id", how="left", validate="one_to_one")
        sample["human_actionable_issue"] = pd.Series([pd.NA] * len(sample), dtype="Int64")
        sample["human_issue_type"] = ""
        sample["human_notes"] = ""
        outputs[name] = sample
    return outputs


def _cache_key(payload: dict[str, Any], prompt: str, schema: dict[str, Any], model: str) -> str:
    raw = json.dumps(
        {"payload": payload, "prompt": prompt, "schema": schema, "model": model},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_live_audit(
    rows: pd.DataFrame,
    prompt_path: Path,
    schema_path: Path,
    cache_dir: Path,
    model: str,
    limit: int | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    from openai import OpenAI

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAIAPI")):
        raise RuntimeError("OPENAI_API_KEY/OPENAIAPI is required for the live semantic audit")
    prompt = prompt_path.read_text(encoding="utf-8")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAIAPI"))
    selected = rows.head(limit) if limit else rows
    def process(row: pd.Series) -> tuple[dict[str, Any], bool, float | None, dict[str, int], str | None]:
        payload = listing_payload(row)
        key = _cache_key(payload, prompt, schema, model)
        cache_path = cache_dir / f"{key}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8")), True, None, {}, None
        started = time.perf_counter()
        try:
            response = client.responses.create(
                model=model,
                instructions=prompt,
                input=json.dumps(payload, ensure_ascii=False),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "inventory_semantic_audit",
                        "schema": schema,
                        "strict": True,
                    }
                },
                store=False,
            )
            result = json.loads(response.output_text)
            jsonschema.validate(result, schema)
            cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            usage = getattr(response, "usage", None)
            tokens = {
                "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
                "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
                "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
            }
            return result, False, time.perf_counter() - started, tokens, str(getattr(response, "model", model))
        except Exception as exc:  # retained as auditable row-level failure
            result = {"spot_id": str(row["spot_id"]), "error": type(exc).__name__, "message": str(exc)}
            return result, False, time.perf_counter() - started, {}, None

    with ThreadPoolExecutor(max_workers=4) as executor:
        processed = list(executor.map(process, [row for _, row in selected.iterrows()]))
    outputs = [item[0] for item in processed]
    cached = sum(item[1] for item in processed)
    latency = [item[2] for item in processed if item[2] is not None]
    errors = sum("error" in item[0] for item in processed)
    token_totals = {
        key: int(sum(item[3].get(key, 0) for item in processed))
        for key in ("input_tokens", "output_tokens", "total_tokens")
    }
    response_models = sorted({item[4] for item in processed if item[4]})
    flattened = []
    for result in outputs:
        issues = result.get("issues", [])
        flattened.append({
            "spot_id": result.get("spot_id"),
            "llm_quality_status": result.get("quality_status"),
            "llm_actionable": any(
                issue.get("classification") in ACTIONABLE and bool(issue.get("actionable"))
                for issue in issues
            ),
            "llm_issue_count": len(issues),
            "llm_result_json": json.dumps(result, ensure_ascii=False),
            "llm_error": result.get("error"),
        })
    pricing = MODEL_PRICING_PER_MILLION.get(model)
    estimated_cost = None
    if pricing:
        estimated_cost = (
            token_totals["input_tokens"] * pricing["input_usd"]
            + token_totals["output_tokens"] * pricing["output_usd"]
        ) / 1_000_000
    meta = {
        "model": model,
        "rows": len(selected),
        "cached_rows": cached,
        "errors": errors,
        "schema_valid_rate": (len(selected) - errors) / len(selected) if len(selected) else None,
        "mean_latency_seconds_uncached": float(np.mean(latency)) if latency else 0.0,
        "usage": token_totals,
        "response_models": response_models,
        "estimated_cost_usd_uncached_calls": estimated_cost,
        "pricing": pricing,
        "cost_status": "ESTIMATED_FROM_PINNED_PUBLIC_TOKEN_RATES" if pricing else "NOT_COMPUTED__MODEL_PRICING_NOT_PINNED",
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "schema_sha256": hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    return pd.DataFrame(flattened), meta


def build_injected_semantic_benchmark(rows: pd.DataFrame | None = None, n_per_class: int = 5, seed: int = 42) -> pd.DataFrame:
    """Fully fabricated controls/contradictions; no repository listing is exported."""
    del rows, seed  # signature retained for callers; inputs are deliberately not inspected.
    aligned = {
        "Land": "Terreno baldío sin construcción para desarrollo futuro.",
        "Office": "Oficina corporativa con salas de juntas y recepción.",
        "Warehouse": "Bodega logística con andenes de carga y altura para racks.",
        "Retail": "Local comercial con aparadores y área de atención al público.",
    }
    contradicted = {
        "Land": "Espacio corporativo terminado con salas de juntas y recepción ejecutiva.",
        "Office": "Terreno baldío sin construcción, ideal para desarrollo desde cero.",
        "Warehouse": "Local comercial dentro de plaza con aparadores y atención al público.",
        "Retail": "Nave logística con andenes de carga y altura libre para racks industriales.",
    }
    samples: list[dict[str, Any]] = []
    for sector in aligned:
        for label, text in [(0, aligned[sector]), (1, contradicted[sector])]:
            for index in range(n_per_class):
                samples.append({
                    "spot_id": f"synthetic_{sector.lower()}_{label}_{index}",
                    "sector_name": sector, "type_name": sector, "state": "Estado Ficticio",
                    "municipality": "Municipio Ficticio", "settlement": "Zona Ficticia",
                    "corridor": "Corredor Ficticio", "region": "Región Ficticia",
                    "title": "Caso completamente sintético de QA",
                    "description": text, "area_sqm": 1000, "modality": "rent",
                    "price_sqm_mxn_rent": 100, "price_sqm_mxn_sale": None,
                    "natural_light": "unknown", "luminaires": None, "charging_ports": None,
                    "security_type": "unknown", "floor_level": None, "elevators": None,
                    "vertical_height_m": None, "parking_spaces": None,
                    "building_status": "unknown", "floor_material": "unknown",
                    "amenities": "[]", "human_actionable_issue": label,
                    "benchmark_source": "FULLY_FABRICATED_NO_REPOSITORY_PAYLOAD",
                })
    return pd.DataFrame(samples)


def evaluate_injected_benchmark(rows: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, Any]:
    """Evaluate a controlled task; this does not estimate natural-listing accuracy."""
    rules = rows.apply(rules_only, axis=1, result_type="expand")
    frame = rows[["spot_id", "human_actionable_issue"]].copy(); frame["spot_id"] = frame["spot_id"].astype(str)
    predicted = predictions.copy(); predicted["spot_id"] = predicted["spot_id"].astype(str)
    frame = frame.merge(rules[["spot_id", "rule_actionable"]], on="spot_id", validate="one_to_one")
    frame = frame.merge(predicted[["spot_id", "llm_actionable", "llm_error"]], on="spot_id", how="left", validate="one_to_one")
    frame["llm_actionable"] = frame["llm_actionable"].eq(True)
    valid = frame["llm_error"].isna(); evaluated = frame[valid].copy()
    evaluated["rules_plus_llm"] = evaluated["rule_actionable"] | evaluated["llm_actionable"]
    result: dict[str, Any] = {
        "status": "CONTROLLED_SYNTHETIC_EVALUATION",
        "warning": "Fully fabricated cases validate task behavior and incremental detection, not accuracy on natural Spot2 listings.",
        "n_rows": int(len(frame)), "n_llm_valid": int(valid.sum()),
    }
    y = evaluated["human_actionable_issue"].astype(int)
    for name in ["rule_actionable", "llm_actionable", "rules_plus_llm"]:
        precision, recall, f1, _ = precision_recall_fscore_support(
            y, evaluated[name].astype(int), average="binary", zero_division=0
        )
        result[name] = {"precision": float(precision), "recall": float(recall), "f1": float(f1)}
    result["incremental_recall_points"] = 100 * (
        result["rules_plus_llm"]["recall"] - result["rule_actionable"]["recall"]
    )
    return result


def evaluate_semantic_audit(labels: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, Any]:
    labels = labels.copy()
    predictions = predictions.copy()
    labels["spot_id"] = labels["spot_id"].astype(str)
    predictions["spot_id"] = predictions["spot_id"].astype(str)
    frame = labels[["spot_id", "human_actionable_issue"]].merge(
        predictions, on="spot_id", how="left", validate="one_to_one"
    )
    rule = labels.apply(rules_only, axis=1, result_type="expand")
    frame = frame.merge(rule[["spot_id", "rule_actionable"]], on="spot_id", validate="one_to_one")
    frame["llm_actionable"] = frame["llm_actionable"].eq(True)
    frame["rules_plus_llm"] = frame["rule_actionable"] | frame["llm_actionable"]
    frame["rules_intersection_llm"] = frame["rule_actionable"] & frame["llm_actionable"]
    gold = frame["human_actionable_issue"].isin([0, 1])
    result: dict[str, Any] = {"n_rows": len(frame), "n_gold": int(gold.sum())}
    if not gold.any():
        result["status"] = "INCOMPLETE_NO_HUMAN_GOLD"
        result["positive_flags"] = {
            name: int(frame[name].sum())
            for name in ["rule_actionable", "llm_actionable", "rules_plus_llm", "rules_intersection_llm"]
        }
        return result
    y = frame.loc[gold, "human_actionable_issue"].astype(int)
    result["status"] = "EVALUATED"
    for name in ["rule_actionable", "llm_actionable", "rules_plus_llm", "rules_intersection_llm"]:
        precision, recall, f1, _ = precision_recall_fscore_support(
            y, frame.loc[gold, name].astype(int), average="binary", zero_division=0
        )
        result[name] = {"precision": precision, "recall": recall, "f1": f1}
    result["incremental_recall_points"] = 100 * (
        result["rules_plus_llm"]["recall"] - result["rule_actionable"]["recall"]
    )
    return result
