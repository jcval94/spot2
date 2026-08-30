from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd
from openai import OpenAI

MODEL_DEFAULT = "gpt-5-nano"
INPUT_PRICE_PER_M = 0.05
OUTPUT_PRICE_PER_M = 0.40

SYSTEM_PROMPT = """You audit commercial-real-estate listing semantics.
Deterministic rules already handle literal claims/contradictions. Your job is ONLY the residual semantic layer:
- cross-field coherence that is not reducible to the supplied rule flags;
- sector/copy or use-case mismatch;
- ambiguity where adaptive reuse may make the copy plausible;
- whether a repeatable NEW rule candidate exists.

Do not restate a direct rule conflict as an incremental LLM finding.
Do not infer facts absent from the supplied record.
Marketing claims without a comparable structured field are not errors.
Prefer no issue when evidence is weak.
Return only the required structured output."""

SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "spot_id": {"type": "integer"},
                    "incremental_issue": {"type": "boolean"},
                    "new_rule_candidate": {"type": "boolean"},
                    "semantic_class": {
                        "type": "string",
                        "enum": [
                            "none",
                            "sector_copy_mismatch",
                            "use_case_mismatch",
                            "cross_field_incoherence",
                            "ambiguous_semantics",
                            "other",
                        ],
                    },
                    "actionability": {
                        "type": "string",
                        "enum": ["none", "monitor", "human_review"],
                    },
                    "use_case_family": {
                        "type": "string",
                        "enum": [
                            "generic",
                            "office",
                            "retail",
                            "industrial",
                            "land",
                            "mixed",
                            "unknown",
                        ],
                    },
                    "adaptive_reuse_plausible": {"type": "boolean"},
                    "requires_human_review": {"type": "boolean"},
                    "confidence": {"type": "integer"},
                    "reason_code": {
                        "type": "string",
                        "enum": [
                            "no_incremental_issue",
                            "covered_by_rules",
                            "semantic_mismatch",
                            "plausible_adaptive_reuse",
                            "unverifiable_marketing_claim",
                            "insufficient_evidence",
                        ],
                    },
                },
                "required": [
                    "spot_id",
                    "incremental_issue",
                    "new_rule_candidate",
                    "semantic_class",
                    "actionability",
                    "use_case_family",
                    "adaptive_reuse_plausible",
                    "requires_human_review",
                    "confidence",
                    "reason_code",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def compact_record(row: pd.Series) -> dict:
    amenities = row.get("amenities")
    try:
        amenities = json.loads(amenities) if pd.notna(amenities) else []
    except (TypeError, ValueError, json.JSONDecodeError):
        amenities = []
    return {
        "id": int(row["spot_id"]),
        "txt": str(row["original_text"]),
        "sec": str(row["sector_name"]),
        "typ": str(row["type_name"]),
        "nl": str(row["natural_light"]),
        "security": str(row["security_type"]),
        "park": str(row["parking_spaces"]),
        "status": str(row["building_status"]),
        "floor": str(row["floor_material"]),
        "elev": str(row["elevators"]),
        "vh": str(row["vertical_height_m"]),
        "am": amenities,
        "rule_direct": int(row["rule_direct_conflict_flag"]),
        "rule_land_copy": int(row["rule_land_building_copy_flag"]),
        "rule_ambiguous": int(row["rule_ambiguity_candidate_flag"]),
    }


def batches(df: pd.DataFrame, size: int):
    for start in range(0, len(df), size):
        yield start // size, df.iloc[start : start + size]


def get_api_key() -> str:
    key = os.getenv("OPENAIKEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "No API key found. Set OPENAIKEY (preferred for this experiment) "
            "or OPENAI_API_KEY before running. No API call was made."
        )
    return key


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * INPUT_PRICE_PER_M / 1_000_000
        + output_tokens * OUTPUT_PRICE_PER_M / 1_000_000
    )


def run(args):
    key = get_api_key()
    client = OpenAI(api_key=key)

    source = pd.read_csv(args.input)
    if args.limit:
        source = source.head(args.limit).copy()
    if len(source) > 100 and not args.allow_more_than_100:
        raise RuntimeError(
            "Pilot safety gate: refusing to call more than 100 records. "
            "Pass --allow-more-than-100 only after reviewing the pilot."
        )

    outputs = []
    usage_rows = []

    for batch_idx, part in batches(source, args.batch_size):
        payload = {"records": [compact_record(r) for _, r in part.iterrows()]}

        response = client.responses.create(
            model=args.model,
            instructions=SYSTEM_PROMPT,
            input=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            reasoning={"effort": "minimal"},
            text={
                "verbosity": "low",
                "format": {
                    "type": "json_schema",
                    "name": "spot_semantic_residual_batch",
                    "strict": True,
                    "schema": SCHEMA,
                },
            },
            max_output_tokens=args.max_output_tokens,
            store=False,
        )

        parsed = json.loads(response.output_text)
        result_rows = parsed["results"]
        expected_ids = set(part["spot_id"].astype(int))
        actual_ids = {int(x["spot_id"]) for x in result_rows}
        if expected_ids != actual_ids:
            raise RuntimeError(
                f"Batch {batch_idx}: returned IDs do not match input IDs. "
                f"missing={sorted(expected_ids-actual_ids)} extra={sorted(actual_ids-expected_ids)}"
            )

        input_tokens = int(getattr(response.usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(response.usage, "output_tokens", 0) or 0)
        cost = estimate_cost(input_tokens, output_tokens)

        for x in result_rows:
            x["llm_batch_index"] = batch_idx
            x["llm_model"] = args.model
            x["llm_input_tokens_batch"] = input_tokens
            x["llm_output_tokens_batch"] = output_tokens
            x["llm_estimated_cost_usd_batch"] = cost
            outputs.append(x)

        usage_rows.append(
            {
                "batch_index": batch_idx,
                "n_records": len(part),
                "model": args.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": cost,
            }
        )

    llm = pd.DataFrame(outputs).rename(
        columns={
            "incremental_issue": "llm_incremental_issue",
            "new_rule_candidate": "llm_new_rule_candidate",
            "semantic_class": "llm_semantic_class",
            "actionability": "llm_actionability",
            "use_case_family": "llm_use_case_family",
            "adaptive_reuse_plausible": "llm_adaptive_reuse_plausible",
            "requires_human_review": "llm_requires_human_review",
            "confidence": "llm_confidence",
            "reason_code": "llm_reason_code",
        }
    )
    final = source.merge(llm, on="spot_id", how="left", validate="one_to_one")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(args.output, index=False)

    usage = pd.DataFrame(usage_rows)
    usage.loc[len(usage)] = {
        "batch_index": "TOTAL",
        "n_records": int(usage["n_records"].sum()),
        "model": args.model,
        "input_tokens": int(usage["input_tokens"].sum()),
        "output_tokens": int(usage["output_tokens"].sum()),
        "estimated_cost_usd": float(usage["estimated_cost_usd"].sum()),
    }
    usage.to_csv(args.usage_output, index=False)

    print(final[[
        "spot_id",
        "sample_stratum",
        "original_text",
        "llm_incremental_issue",
        "llm_semantic_class",
        "llm_actionability",
        "llm_new_rule_candidate",
        "llm_confidence",
    ]].head(20).to_string(index=False))
    print("\nUsage:")
    print(usage.to_string(index=False))


def parse_args():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=root / "data" / "pilot_input_100.csv")
    p.add_argument("--output", type=Path, default=root / "results" / "pilot_llm_results_100.csv")
    p.add_argument("--usage-output", type=Path, default=root / "results" / "pilot_usage_summary.csv")
    p.add_argument("--model", default=MODEL_DEFAULT)
    p.add_argument("--batch-size", type=int, default=20)
    p.add_argument("--max-output-tokens", type=int, default=2500)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--allow-more-than-100", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
