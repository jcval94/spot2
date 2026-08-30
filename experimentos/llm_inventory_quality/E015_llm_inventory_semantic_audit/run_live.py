from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.openai_auditor import PROMPT_PATH, SCHEMA_PATH, audit, build_payload, input_hash, model_name


HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "labeling" / "labeling_holdout_v2.csv"
DEFAULT_OUTPUT = HERE / "results" / "llm_predictions.jsonl"


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default=model_name())
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    rows = load_rows(args.input)
    if args.limit is not None:
        rows = rows[: args.limit]

    cache = {} if args.force else load_cache(args.output)
    results = dict(cache)
    for i, row in enumerate(rows, 1):
        payload = build_payload(row)
        key = input_hash(payload, args.model, prompt, schema)
        if key in results and not args.force:
            continue
        try:
            record = audit(payload, model=args.model)
        except Exception as exc:
            record = {"status": "error", "error_type": type(exc).__name__, "error": str(exc), "model": args.model}
        record.update({"spot_id": str(row["spot_id"]), "input_hash": key})
        results[key] = record
        print(f"[{i}/{len(rows)}] spot_id={row['spot_id']} status={record['status']}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(results.values(), key=lambda x: int(x["spot_id"]))
    args.output.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in ordered) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
