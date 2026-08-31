from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import time
import unicodedata
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT / "data" / "candidate" / "csv"
PROMPT_PATH = HERE / "prompt.md"
SCHEMA_PATH = HERE / "response.schema.json"
CACHE_DIR = HERE / "cache"
RESULTS_DIR = HERE / "results"

DEFAULT_MODEL = "gpt-5-nano"
# Historical/current published GPT-5 nano text pricing used by E017:
# USD 0.05 / 1M input tokens, USD 0.40 / 1M output tokens.
KNOWN_PRICING_USD_PER_M = {
    "gpt-5-nano": {"input": 0.05, "output": 0.40},
}

NATURAL = ("iluminacion natural", "luz natural")
SECURITY = ("seguridad 24/7", "control de acceso", "vigilancia", "circuito cerrado")
PARKING = ("estacionamiento", "cajon de estacionamiento", "cajones de estacionamiento", "parking")
READINESS = ("listo para ocupar", "recien remodelado", "acabados modernos", "acabados de primera")
BUILDING_COPY = tuple(sorted(set(NATURAL + READINESS)))
OFFICE_DISTRIBUTION = ("ideal para oficinas corporativas o centro de distribucion",)

ALLOWED = {
    "residual_class": {"no_residual_issue", "residual_ambiguous", "residual_actionable"},
    "semantic_class": {"none", "sector_copy_mismatch", "use_case_mismatch", "cross_field_incoherence", "ambiguous_semantics", "other"},
    "use_case_family": {"generic", "office", "retail", "industrial", "land", "mixed", "unknown"},
    "pattern_candidate": {"none", "review_candidate"},
    "confidence": {"low", "medium", "high"},
    "reason_code": {
        "no_incremental_issue",
        "covered_by_rules",
        "semantic_mismatch",
        "plausible_adaptive_reuse",
        "unverifiable_marketing_claim",
        "insufficient_evidence",
    },
}
REQUIRED_OUTPUT = {
    "spot_id",
    "residual_class",
    "semantic_class",
    "use_case_family",
    "adaptive_reuse_plausible",
    "pattern_candidate",
    "confidence",
    "evidence_text",
    "reason_code",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        if fieldnames:
            with path.open("w", encoding="utf-8", newline="") as fh:
                csv.DictWriter(fh, fieldnames=fieldnames).writeheader()
        return
    fieldnames = fieldnames or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def has_any(text: str, phrases: Iterable[str]) -> bool:
    x = norm(text)
    return any(p in x for p in phrases)


def parse_bool(value: Any) -> bool | None:
    x = norm(value).strip()
    if x == "true":
        return True
    if x == "false":
        return False
    return None


def parse_number(value: Any) -> float | int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return int(x) if x.is_integer() else x


def parse_amenities(value: Any) -> list[str]:
    if value is None or str(value).strip() == "":
        return []
    try:
        x = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    return [str(v) for v in x] if isinstance(x, list) else []


def load_listing_rows() -> list[dict[str, Any]]:
    spots = read_csv(RAW / "spots.csv")
    attrs = {int(r["spot_id"]): r for r in read_csv(RAW / "spot_attributes.csv")}
    rows: list[dict[str, Any]] = []
    for spot in spots:
        sid = int(spot["spot_id"])
        attr = attrs.get(sid)
        if attr is None:
            raise RuntimeError(f"Missing spot_attributes for spot_id={sid}")
        rows.append({**spot, **{f"attr__{k}": v for k, v in attr.items() if k != "spot_id"}})
    return rows


def rules_for(row: dict[str, Any]) -> dict[str, Any]:
    text = f"{row.get('title', '')}\n{row.get('description', '')}"
    natural_light = parse_bool(row.get("attr__natural_light"))
    security_type = norm(row.get("attr__security_type"))
    parking_spaces = parse_number(row.get("attr__parking_spaces"))
    building_status = norm(row.get("attr__building_status"))
    amenities = {norm(x) for x in parse_amenities(row.get("attr__amenities"))}

    claim_natural = has_any(text, NATURAL)
    claim_security = has_any(text, SECURITY)
    claim_parking = has_any(text, PARKING)
    claim_readiness = has_any(text, READINESS)

    conflict_natural = int(claim_natural and natural_light is False)
    conflict_security = int(claim_security and security_type in {"", "none"})
    conflict_parking = int(
        claim_parking
        and (parking_spaces is None or float(parking_spaces) == 0.0)
        and "parking" not in amenities
    )
    conflict_readiness = int(claim_readiness and building_status == "needs_renovation")
    direct_count = conflict_natural + conflict_security + conflict_parking + conflict_readiness
    direct_flag = int(direct_count > 0)

    land_copy = int(str(row.get("sector_name")) == "Land" and has_any(text, BUILDING_COPY))
    security_ambiguity = int(claim_security and security_type in {"basic", "cctv"})
    retail_adaptive = int(str(row.get("sector_name")) == "Retail" and has_any(text, OFFICE_DISTRIBUTION))
    semantic_ambiguity = int(bool(security_ambiguity or retail_adaptive))
    signal_count = direct_flag + land_copy + semantic_ambiguity

    tier = "none"
    if semantic_ambiguity:
        tier = "ambiguity"
    if land_copy:
        tier = "cross_field"
    if direct_flag:
        tier = "direct_conflict"

    return {
        "spot_id": int(row["spot_id"]),
        "rule_conflict_natural_light": conflict_natural,
        "rule_conflict_security": conflict_security,
        "rule_conflict_parking": conflict_parking,
        "rule_conflict_readiness": conflict_readiness,
        "rule_direct_conflict_count": direct_count,
        "rule_direct_conflict_flag": direct_flag,
        "rule_land_building_copy_flag": land_copy,
        "rule_security_ambiguity_flag": security_ambiguity,
        "rule_retail_adaptive_use_flag": retail_adaptive,
        "rule_semantic_ambiguity_flag": semantic_ambiguity,
        "rule_semantic_signal_count": signal_count,
        "rule_semantic_review_tier": tier,
    }


def reproduce_rules(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sidecar = [rules_for(row) for row in rows]
    n = len(sidecar)

    def count(col: str, predicate=lambda x: bool(int(x))) -> int:
        return sum(1 for r in sidecar if predicate(r[col]))

    tiers: dict[str, int] = {}
    for r in sidecar:
        tiers[r["rule_semantic_review_tier"]] = tiers.get(r["rule_semantic_review_tier"], 0) + 1

    summary = {
        "n_listings": n,
        "rule_direct_conflict_flag": count("rule_direct_conflict_flag"),
        "rule_land_building_copy_flag": count("rule_land_building_copy_flag"),
        "rule_security_ambiguity_flag": count("rule_security_ambiguity_flag"),
        "rule_retail_adaptive_use_flag": count("rule_retail_adaptive_use_flag"),
        "rule_semantic_ambiguity_flag": count("rule_semantic_ambiguity_flag"),
        "at_least_one_semantic_signal": count("rule_semantic_signal_count", lambda x: int(x) >= 1),
        "two_simultaneous_semantic_signals": count("rule_semantic_signal_count", lambda x: int(x) >= 2),
        "review_tiers": tiers,
    }
    return sidecar, summary


def build_payload(row: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    return {
        "spot_id": int(row["spot_id"]),
        "sector_name": row.get("sector_name") or None,
        "type_name": row.get("type_name") or None,
        "modality": row.get("modality") or None,
        "title": row.get("title") or "",
        "description": row.get("description") or "",
        "attributes": {
            "natural_light": parse_bool(row.get("attr__natural_light")),
            "security_type": row.get("attr__security_type") or None,
            "parking_spaces": parse_number(row.get("attr__parking_spaces")),
            "building_status": row.get("attr__building_status") or None,
            "amenities": parse_amenities(row.get("attr__amenities")),
        },
        "deterministic_rules": {
            k: v
            for k, v in rules.items()
            if k != "spot_id"
        },
    }


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def request_hash(model: str, prompt: str, schema: dict[str, Any], payload: dict[str, Any]) -> str:
    return canonical_hash({"model": model, "prompt": prompt, "schema": schema, "payload": payload})


def validate_output(x: dict[str, Any], expected_spot_id: int) -> None:
    if set(x) != REQUIRED_OUTPUT:
        raise ValueError(f"Structured output keys mismatch: {sorted(set(x) ^ REQUIRED_OUTPUT)}")
    if not isinstance(x["spot_id"], int) or x["spot_id"] != expected_spot_id:
        raise ValueError(f"spot_id mismatch: expected {expected_spot_id}, got {x.get('spot_id')}")
    for key, allowed in ALLOWED.items():
        if x[key] not in allowed:
            raise ValueError(f"{key}={x[key]!r} outside allowed enum")
    if not isinstance(x["adaptive_reuse_plausible"], bool):
        raise ValueError("adaptive_reuse_plausible must be boolean")
    if not isinstance(x["evidence_text"], str):
        raise ValueError("evidence_text must be string")
    if x["residual_class"] == "no_residual_issue" and x["pattern_candidate"] != "none":
        raise ValueError("no_residual_issue cannot be a pattern candidate")
    if x["pattern_candidate"] == "review_candidate" and x["residual_class"] != "residual_actionable":
        raise ValueError("review_candidate requires residual_actionable")


def price_for(args: argparse.Namespace) -> tuple[float, float]:
    if args.input_price_per_m is not None and args.output_price_per_m is not None:
        return args.input_price_per_m, args.output_price_per_m
    if args.model not in KNOWN_PRICING_USD_PER_M:
        raise RuntimeError(
            f"No frozen price table for model {args.model!r}. "
            "Pass --input-price-per-m and --output-price-per-m explicitly."
        )
    p = KNOWN_PRICING_USD_PER_M[args.model]
    return p["input"], p["output"]


def actual_cost(input_tokens: int, output_tokens: int, input_price: float, output_price: float) -> float:
    return input_tokens * input_price / 1_000_000 + output_tokens * output_price / 1_000_000


def conservative_request_reservation(
    prompt: str,
    schema: dict[str, Any],
    payload: dict[str, Any],
    max_output_tokens: int,
    input_price: float,
    output_price: float,
) -> float:
    # No tokenizer dependency: chars/2 intentionally over-reserves relative to typical English/Spanish text.
    material = prompt + json.dumps(schema, ensure_ascii=False) + json.dumps(payload, ensure_ascii=False)
    estimated_input_tokens = math.ceil(len(material) / 2)
    return actual_cost(estimated_input_tokens, max_output_tokens, input_price, output_price)


def api_key() -> str:
    value = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAIKEY") or os.getenv("OPENAIAPI")
    if not value:
        raise RuntimeError("No OpenAI API key found. No API call was made.")
    return value


def cached_or_live(
    *,
    args: argparse.Namespace,
    payload: dict[str, Any],
    prompt: str,
    schema: dict[str, Any],
    spent: float,
    input_price: float,
    output_price: float,
) -> tuple[dict[str, Any], float, bool]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    h = request_hash(args.model, prompt, schema, payload)
    cache_path = CACHE_DIR / f"{h}.json"
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        validate_output(cached["output"], int(payload["spot_id"]))
        return cached, spent, True

    reservation = conservative_request_reservation(
        prompt, schema, payload, args.max_output_tokens, input_price, output_price
    )
    if spent + reservation > args.hard_budget_usd + 1e-12:
        raise RuntimeError(
            f"Hard budget guard stopped before request for spot_id={payload['spot_id']}: "
            f"spent={spent:.6f}, reserved_next={reservation:.6f}, cap={args.hard_budget_usd:.6f}"
        )

    from openai import OpenAI  # Optional dependency: imported only for --mode live.

    client = OpenAI(api_key=api_key())
    last_error: Exception | None = None
    for attempt in range(args.max_retries + 1):
        try:
            started = time.perf_counter()
            response = client.responses.create(
                model=args.model,
                instructions=prompt,
                input=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                reasoning={"effort": "minimal"},
                text={
                    "verbosity": "low",
                    "format": {
                        "type": "json_schema",
                        "name": "semantic_inventory_residual",
                        "strict": True,
                        "schema": schema,
                    },
                },
                max_output_tokens=args.max_output_tokens,
                store=False,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            output = json.loads(response.output_text)
            validate_output(output, int(payload["spot_id"]))
            usage = getattr(response, "usage", None)
            input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
            cost = actual_cost(input_tokens, output_tokens, input_price, output_price)
            spent_after = spent + cost
            if spent_after > args.hard_budget_usd + 1e-12:
                raise RuntimeError(
                    f"Observed cost exceeded hard budget after response: {spent_after:.6f} > {args.hard_budget_usd:.6f}"
                )
            record = {
                "request_hash": h,
                "model": args.model,
                "prompt_sha256": canonical_hash(prompt),
                "schema_sha256": canonical_hash(schema),
                "payload_sha256": canonical_hash(payload),
                "response_id": getattr(response, "id", None),
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": cost,
                "input_price_per_m": input_price,
                "output_price_per_m": output_price,
                "output": output,
            }
            cache_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return record, spent_after, False
        except Exception as exc:  # retry only the same frozen request
            last_error = exc
            if attempt >= args.max_retries:
                raise
            time.sleep(args.retry_sleep_seconds)
    raise RuntimeError(str(last_error))


def evaluate_outputs(
    source_by_id: dict[int, dict[str, Any]],
    rule_by_id: dict[int, dict[str, Any]],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    outputs = [r["output"] for r in records]
    ids = [int(x["spot_id"]) for x in outputs]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate spot_id in evaluated LLM outputs")

    counts = {k: 0 for k in ["no_residual_issue", "residual_ambiguous", "residual_actionable"]}
    pattern_candidates = 0
    rule_overlap = 0
    for x in outputs:
        counts[x["residual_class"]] += 1
        pattern_candidates += int(x["pattern_candidate"] == "review_candidate")
        rule_overlap += int(rule_by_id[int(x["spot_id"])]["rule_semantic_signal_count"] > 0)

    result: dict[str, Any] = {
        "n_outputs": len(outputs),
        "technical_schema_valid": len(outputs),
        "technical_schema_valid_rate": 1.0 if outputs else None,
        "residual_class_counts": counts,
        "rules_overlap_count": rule_overlap,
        "rules_overlap_rate": rule_overlap / len(outputs) if outputs else None,
        "pattern_candidates": pattern_candidates,
        "candidate_novelty_status": "CANDIDATE_ONLY_REQUIRES_HUMAN_VALIDATION",
        "human_precision": None,
        "human_recall": None,
        "human_metrics_status": "UNAVAILABLE_NO_HUMAN_GOLD",
    }

    # Optional pattern-challenge metric. This is NOT human gold.
    labeled = []
    for x in outputs:
        src = source_by_id[int(x["spot_id"])]
        label = src.get("challenge_pattern_label")
        if label not in (None, ""):
            labeled.append((int(str(label)), int(x["residual_class"] == "residual_actionable")))
    if labeled:
        tp = sum(1 for y, p in labeled if y == 1 and p == 1)
        tn = sum(1 for y, p in labeled if y == 0 and p == 0)
        fp = sum(1 for y, p in labeled if y == 0 and p == 1)
        fn = sum(1 for y, p in labeled if y == 1 and p == 0)
        result["challenge_pattern_comparator"] = {
            "n": len(labeled),
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "sensitivity_vs_pattern": tp / (tp + fn) if tp + fn else None,
            "specificity_vs_pattern": tn / (tn + fp) if tn + fp else None,
            "warning": "Pattern comparator only; not human precision/recall.",
        }
    else:
        result["challenge_pattern_comparator"] = None
    return result


def run_rules() -> None:
    rows = load_listing_rows()
    sidecar, summary = reproduce_rules(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(RESULTS_DIR / "rules_sidecar_3000.csv", sidecar)
    (RESULTS_DIR / "rules_baseline_reproduction.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


def run_live(args: argparse.Namespace) -> None:
    rows = load_listing_rows()
    sidecar, summary = reproduce_rules(rows)
    rule_by_id = {int(r["spot_id"]): r for r in sidecar}
    source_by_id = {int(r["spot_id"]): r for r in rows}

    if args.include_known_rule_hits:
        candidates = rows
    else:
        candidates = [r for r in rows if rule_by_id[int(r["spot_id"])]["rule_semantic_signal_count"] == 0]

    candidates = sorted(candidates, key=lambda r: int(r["spot_id"]))
    if args.limit is not None:
        candidates = candidates[: args.limit]
    if len(candidates) > args.hard_max_records and not args.allow_more_than_hard_max:
        raise RuntimeError(
            f"Safety gate: refusing {len(candidates)} records; hard max is {args.hard_max_records}. "
            "Use --allow-more-than-hard-max only after reviewing a smaller run."
        )

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    input_price, output_price = price_for(args)

    spent = 0.0
    records: list[dict[str, Any]] = []
    usage_rows: list[dict[str, Any]] = []
    for row in candidates:
        sid = int(row["spot_id"])
        payload = build_payload(row, rule_by_id[sid])
        record, spent, cache_hit = cached_or_live(
            args=args,
            payload=payload,
            prompt=prompt,
            schema=schema,
            spent=spent,
            input_price=input_price,
            output_price=output_price,
        )
        records.append(record)
        usage_rows.append({
            "spot_id": sid,
            "model": args.model,
            "cache_hit": cache_hit,
            "input_tokens": record.get("input_tokens", 0),
            "output_tokens": record.get("output_tokens", 0),
            "estimated_cost_usd": 0.0 if cache_hit else record.get("estimated_cost_usd", 0.0),
            "request_hash": record["request_hash"],
        })

    evaluation = evaluate_outputs(source_by_id, rule_by_id, records)
    evaluation["rules_baseline_reproduction"] = summary
    evaluation["model"] = args.model
    evaluation["new_api_cost_usd"] = spent
    evaluation["hard_budget_usd"] = args.hard_budget_usd
    evaluation["note"] = "human precision/recall remain unavailable unless a separate human-gold set is supplied."

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(
        RESULTS_DIR / "live_usage.csv",
        usage_rows,
        ["spot_id", "model", "cache_hit", "input_tokens", "output_tokens", "estimated_cost_usd", "request_hash"],
    )
    (RESULTS_DIR / "live_evaluation.json").write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(evaluation, indent=2))


def evaluate_cache(args: argparse.Namespace) -> None:
    rows = load_listing_rows()
    sidecar, summary = reproduce_rules(rows)
    rule_by_id = {int(r["spot_id"]): r for r in sidecar}
    source_by_id = {int(r["spot_id"]): r for r in rows}
    records: list[dict[str, Any]] = []
    for path in sorted(CACHE_DIR.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        output = record["output"]
        sid = int(output["spot_id"])
        if sid not in source_by_id:
            continue
        validate_output(output, sid)
        records.append(record)
    evaluation = evaluate_outputs(source_by_id, rule_by_id, records)
    evaluation["rules_baseline_reproduction"] = summary
    evaluation["cache_records"] = len(records)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "cache_evaluation.json").write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(evaluation, indent=2))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rules-first semantic Inventory/Catalog QA audit")
    p.add_argument("--mode", choices=["rules", "live", "evaluate-cache"], default="rules")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--hard-max-records", type=int, default=100)
    p.add_argument("--allow-more-than-hard-max", action="store_true")
    p.add_argument("--include-known-rule-hits", action="store_true")
    p.add_argument("--hard-budget-usd", type=float, default=0.10)
    p.add_argument("--input-price-per-m", type=float)
    p.add_argument("--output-price-per-m", type=float)
    p.add_argument("--max-output-tokens", type=int, default=500)
    p.add_argument("--max-retries", type=int, default=1)
    p.add_argument("--retry-sleep-seconds", type=float, default=1.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "rules":
        run_rules()
    elif args.mode == "live":
        run_live(args)
    else:
        evaluate_cache(args)


if __name__ == "__main__":
    main()
