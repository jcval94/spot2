from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

from client import audit, load_prompt_schema


MODEL = "gpt-5-mini"
INPUT_PRICE_PER_M = 0.25
OUTPUT_PRICE_PER_M = 2.00
MAX_OUTPUT_TOKENS = 1600
TRANSIENT = {
    "RateLimitError",
    "APIConnectionError",
    "APITimeoutError",
    "InternalServerError"
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    if str(value).lower() == "true":
        return True
    if str(value).lower() == "false":
        return False
    return None


def parse_number(value: str | None) -> int | float | None:
    if value is None or value == "":
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def build_payload(row: dict[str, str]) -> dict[str, Any]:
    try:
        amenities = json.loads(row.get("amenities", "[]"))
    except json.JSONDecodeError:
        amenities = []
    return {
        "spot_id": str(row["spot_id"]),
        "sector_name": row.get("sector_name"),
        "type_name": row.get("type_name"),
        "modality": row.get("modality"),
        "title": row.get("title"),
        "description": row.get("description"),
        "attributes": {
            "natural_light": parse_bool(row.get("natural_light")),
            "security_type": row.get("security_type") or None,
            "parking_spaces": parse_number(row.get("parking_spaces")),
            "building_status": row.get("building_status") or None,
            "amenities": amenities
        }
    }


def input_hash(payload: dict[str, Any], prompt: str, schema: dict[str, Any]) -> str:
    raw = json.dumps(
        {"model": MODEL, "prompt": prompt, "schema": schema, "payload": payload},
        sort_keys=True,
        ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            obj = json.loads(line)
            out[obj["input_hash"]] = obj
    return out


def write_jsonl(path: Path, results: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(results.values(), key=lambda x: int(x["spot_id"]))
    path.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n",
        encoding="utf-8"
    )


def load_budget(path: Path, budget: float) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "hard_budget_usd": budget,
        "reserved_max_cost_usd": 0.0,
        "actual_success_cost_usd": 0.0,
        "attempts": 0,
        "successes": 0,
        "failures": 0,
        "budget_exhausted": false
    }


def save_budget(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def reserve_cost(payload: dict[str, Any], prompt: str, schema: dict[str, Any]) -> float:
    chars = len(prompt) + len(json.dumps(schema)) + len(json.dumps(payload))
    estimated_input_tokens = max(1, math.ceil(chars / 3))
    return (
        estimated_input_tokens / 1_000_000 * INPUT_PRICE_PER_M
        + MAX_OUTPUT_TOKENS / 1_000_000 * OUTPUT_PRICE_PER_M
    )


def actual_cost(record: dict[str, Any]) -> float:
    return (
        int(record.get("input_tokens") or 0) / 1_000_000 * INPUT_PRICE_PER_M
        + int(record.get("output_tokens") or 0) / 1_000_000 * OUTPUT_PRICE_PER_M
    )


def safe_error(exc: Exception) -> str:
    return str(exc).replace("\n", " ").replace("\r", " ")[:500]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--budget-state", type=Path, required=True)
    p.add_argument("--budget-usd", type=float, default=2.0)
    p.add_argument("--limit", type=int)
    p.add_argument("--max-error-rate", type=float, default=0.02)
    p.add_argument("--max-attempts", type=int, default=3)
    args = p.parse_args()

    prompt, schema = load_prompt_schema()
    rows = read_rows(args.input)
    if args.limit is not None:
        rows = rows[: args.limit]

    results = load_jsonl(args.output)
    budget = load_budget(args.budget_state, args.budget_usd)
    attempted = errors = 0

    for idx, row in enumerate(rows, 1):
        payload = build_payload(row)
        key = input_hash(payload, prompt, schema)
        if key in results:
            continue
        attempted += 1
        final = None

        for attempt in range(1, args.max_attempts + 1):
            reserve = reserve_cost(payload, prompt, schema)
            if budget["reserved_max_cost_usd"] + reserve > args.budget_usd:
                budget["budget_exhausted"] = True
                save_budget(args.budget_state, budget)
                write_jsonl(args.output, results)
                print(
                    f"BUDGET_STOP before spot_id={row['spot_id']} "
                    f"reserved={budget['reserved_max_cost_usd']:.6f}/"
                    f"{args.budget_usd:.2f}"
                )
                return 0

            budget["reserved_max_cost_usd"] += reserve
            budget["attempts"] += 1
            save_budget(args.budget_state, budget)

            try:
                final = audit(payload, model=MODEL)
                final["attempt"] = attempt
                budget["successes"] += 1
                budget["actual_success_cost_usd"] += actual_cost(final)
                break
            except Exception as exc:
                error_type = type(exc).__name__
                print(
                    f"[{idx}/{len(rows)}] spot_id={row['spot_id']} "
                    f"attempt={attempt} error_type={error_type} "
                    f"error={safe_error(exc)}"
                )
                if error_type not in TRANSIENT or attempt == args.max_attempts:
                    final = {
                        "status": "error",
                        "model": MODEL,
                        "attempt": attempt,
                        "error_type": error_type,
                        "error": safe_error(exc)
                    }
                    budget["failures"] += 1
                    break
                time.sleep(min(2 ** attempt, 8))

        assert final is not None
        final.update({"spot_id": str(row["spot_id"]), "input_hash": key})
        results[key] = final
        errors += int(final["status"] != "ok")
        save_budget(args.budget_state, budget)
        write_jsonl(args.output, results)
        print(
            f"[{idx}/{len(rows)}] spot_id={row['spot_id']} "
            f"status={final['status']} "
            f"reserved={budget['reserved_max_cost_usd']:.6f}/"
            f"{args.budget_usd:.2f}"
        )

    error_rate = errors / attempted if attempted else 0.0
    print(
        f"LIVE_SUMMARY attempted={attempted} errors={errors} "
        f"error_rate={error_rate:.4f} "
        f"actual_cost={budget['actual_success_cost_usd']:.6f} "
        f"reserved={budget['reserved_max_cost_usd']:.6f}"
    )
    return 3 if error_rate > args.max_error_rate else 0


if __name__ == "__main__":
    raise SystemExit(main())
