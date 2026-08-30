from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any

from src.openai_auditor import (
    PROMPT_PATH,
    SCHEMA_PATH,
    audit,
    build_payload,
    input_hash,
    model_name,
)


HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "labeling" / "labeling_holdout_v2.csv"
DEFAULT_OUTPUT = HERE / "results" / "llm_predictions.jsonl"
DEFAULT_BUDGET_STATE = HERE / "results" / "live_budget.json"

PRICE_PER_M_INPUT = {"gpt-5-nano": 0.05}
PRICE_PER_M_OUTPUT = {"gpt-5-nano": 0.40}
MAX_OUTPUT_TOKENS = 1600

TRANSIENT_ERROR_TYPES = {
    "RateLimitError",
    "APIConnectionError",
    "APITimeoutError",
    "InternalServerError",
}


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["input_hash"]] = row
    return out


def load_budget(path: Path, budget_usd: float) -> dict[str, Any]:
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
        state["budget_usd"] = min(float(state.get("budget_usd", budget_usd)), budget_usd)
        return state
    return {
        "budget_usd": budget_usd,
        "reserved_max_cost_usd": 0.0,
        "actual_success_cost_usd": 0.0,
        "attempts": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "budget_exhausted": False,
    }


def save_budget(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def estimated_input_tokens(payload: dict[str, Any], prompt: str, schema: dict[str, Any]) -> int:
    # Conservative approximation for the budget guard. /3 deliberately
    # overestimates common English/JSON tokenization versus the usual /4 heuristic.
    chars = len(prompt) + len(json.dumps(schema, ensure_ascii=False)) + len(
        json.dumps(payload, ensure_ascii=False)
    )
    return max(1, math.ceil(chars / 3))


def max_call_cost_usd(
    payload: dict[str, Any],
    prompt: str,
    schema: dict[str, Any],
    model: str,
) -> float:
    if model not in PRICE_PER_M_INPUT or model not in PRICE_PER_M_OUTPUT:
        raise ValueError(
            f"No pricing guard configured for model={model}. "
            "Refusing live execution without an explicit price."
        )
    return (
        estimated_input_tokens(payload, prompt, schema)
        / 1_000_000
        * PRICE_PER_M_INPUT[model]
        + MAX_OUTPUT_TOKENS / 1_000_000 * PRICE_PER_M_OUTPUT[model]
    )


def actual_cost_usd(record: dict[str, Any], model: str) -> float:
    return (
        int(record.get("input_tokens") or 0)
        / 1_000_000
        * PRICE_PER_M_INPUT[model]
        + int(record.get("output_tokens") or 0)
        / 1_000_000
        * PRICE_PER_M_OUTPUT[model]
    )


def write_results(path: Path, results: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(results.values(), key=lambda x: int(x["spot_id"]))
    path.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in ordered) + "\n",
        encoding="utf-8",
    )


def safe_error(exc: Exception) -> str:
    message = str(exc).replace("\n", " ").replace("\r", " ")
    return message[:500]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default=model_name())
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=1.70)
    parser.add_argument("--budget-state", type=Path, default=DEFAULT_BUDGET_STATE)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--max-error-rate", type=float, default=1.0)
    args = parser.parse_args()

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    rows = load_rows(args.input)
    if args.limit is not None:
        rows = rows[: args.limit]

    cache = {} if args.force else load_cache(args.output)
    results = dict(cache)
    budget = load_budget(args.budget_state, args.budget_usd)

    attempted_rows = 0
    error_rows = 0

    for i, row in enumerate(rows, 1):
        payload = build_payload(row)
        key = input_hash(payload, args.model, prompt, schema)
        if key in results and not args.force:
            continue

        attempted_rows += 1
        final_record: dict[str, Any] | None = None

        for attempt in range(1, args.max_attempts + 1):
            reserve = max_call_cost_usd(payload, prompt, schema, args.model)
            if budget["reserved_max_cost_usd"] + reserve > args.budget_usd:
                budget["budget_exhausted"] = True
                save_budget(args.budget_state, budget)
                write_results(args.output, results)
                print(
                    f"BUDGET_STOP budget_usd={args.budget_usd:.4f} "
                    f"reserved_max_cost_usd={budget['reserved_max_cost_usd']:.6f} "
                    f"before spot_id={row['spot_id']}"
                )
                return 0

            budget["reserved_max_cost_usd"] += reserve
            budget["attempts"] += 1
            save_budget(args.budget_state, budget)

            try:
                record = audit(payload, model=args.model)
                record["attempt"] = attempt
                budget["successful_calls"] += 1
                budget["actual_success_cost_usd"] += actual_cost_usd(record, args.model)
                final_record = record
                break
            except Exception as exc:
                error_type = type(exc).__name__
                message = safe_error(exc)
                print(
                    f"[{i}/{len(rows)}] spot_id={row['spot_id']} "
                    f"attempt={attempt}/{args.max_attempts} "
                    f"error_type={error_type} error={message}"
                )
                if error_type not in TRANSIENT_ERROR_TYPES or attempt >= args.max_attempts:
                    final_record = {
                        "status": "error",
                        "error_type": error_type,
                        "error": message,
                        "model": args.model,
                        "attempt": attempt,
                    }
                    budget["failed_calls"] += 1
                    break
                time.sleep(min(2 ** attempt, 8))

        assert final_record is not None
        final_record.update({"spot_id": str(row["spot_id"]), "input_hash": key})
        results[key] = final_record
        if final_record["status"] == "error":
            error_rows += 1

        save_budget(args.budget_state, budget)
        write_results(args.output, results)
        print(
            f"[{i}/{len(rows)}] spot_id={row['spot_id']} "
            f"status={final_record['status']} "
            f"budget_reserved={budget['reserved_max_cost_usd']:.6f}/"
            f"{args.budget_usd:.2f}"
        )

    error_rate = error_rows / attempted_rows if attempted_rows else 0.0
    print(
        f"LIVE_SUMMARY attempted_rows={attempted_rows} errors={error_rows} "
        f"error_rate={error_rate:.4f} "
        f"actual_success_cost_usd={budget['actual_success_cost_usd']:.6f} "
        f"reserved_max_cost_usd={budget['reserved_max_cost_usd']:.6f}"
    )
    if error_rate > args.max_error_rate:
        print(
            f"ERROR_RATE_GATE failed: {error_rate:.4f} > "
            f"{args.max_error_rate:.4f}"
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
