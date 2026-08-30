from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd
from openai import OpenAI

from run_pilot import (
    INPUT_PRICE_PER_M,
    MODEL_DEFAULT,
    OUTPUT_PRICE_PER_M,
    compact_record,
    estimate_cost,
)

SYSTEM_PROMPT_V2 = """You audit residual semantics in commercial-real-estate listings.
Literal claims and direct contradictions are already handled by deterministic rules supplied in each record.
Classify ONLY what remains after those rules.

novelty meanings:
- no_residual_issue: no meaningful semantic issue remains.
- covered_by_rules: the apparent problem is already captured by supplied rule flags.
- residual_ambiguous: a real semantic ambiguity remains, but adaptive reuse or missing ontology prevents calling it actionable.
- residual_actionable: a cross-field semantic issue remains that should be reviewed and is not already captured by the supplied rules.

Constraints:
- If novelty is no_residual_issue or covered_by_rules, residual_type MUST be none and new_rule_candidate MUST be false.
- new_rule_candidate may be true only for a residual_* novelty and only when the pattern looks reusable across multiple listings.
- Marketing claims without comparable structured fields are not issues.
- Do not invent facts.
Return only the strict structured output."""

SCHEMA_V2 = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "spot_id": {"type": "integer"},
                    "novelty": {
                        "type": "string",
                        "enum": [
                            "no_residual_issue",
                            "covered_by_rules",
                            "residual_ambiguous",
                            "residual_actionable",
                        ],
                    },
                    "residual_type": {
                        "type": "string",
                        "enum": [
                            "none",
                            "sector_copy_mismatch",
                            "use_case_mismatch",
                            "cross_field_incoherence",
                            "other",
                        ],
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
                    "new_rule_candidate": {"type": "boolean"},
                    "confidence": {"type": "integer"},
                },
                "required": [
                    "spot_id",
                    "novelty",
                    "residual_type",
                    "use_case_family",
                    "adaptive_reuse_plausible",
                    "new_rule_candidate",
                    "confidence",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def get_api_key() -> str:
    key = os.getenv("OPENAIKEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAIKEY or OPENAI_API_KEY. No API call was made.")
    return key


def validate_logic(x: dict) -> None:
    novelty = x["novelty"]
    residual = x["residual_type"]
    candidate = x["new_rule_candidate"]
    if novelty in {"no_residual_issue", "covered_by_rules"}:
        if residual != "none" or candidate:
            raise ValueError(f"Contradictory V2 output: {x}")
    if novelty.startswith("residual_") and residual == "none":
        raise ValueError(f"Residual novelty requires residual_type: {x}")
    if candidate and not novelty.startswith("residual_"):
        raise ValueError(f"New rule candidate must be residual: {x}")


def run(args):
    source = pd.read_csv(args.input).head(args.limit).copy()
    if len(source) > 100:
        raise RuntimeError("V2 pilot is hard-limited to 100 rows.")

    client = OpenAI(api_key=get_api_key())
    outputs, usage_rows = [], []

    for batch_idx, start in enumerate(range(0, len(source), args.batch_size)):
        part = source.iloc[start : start + args.batch_size]
        payload = {"records": [compact_record(r) for _, r in part.iterrows()]}
        response = client.responses.create(
            model=args.model,
            instructions=SYSTEM_PROMPT_V2,
            input=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            reasoning={"effort": "minimal"},
            text={
                "verbosity": "low",
                "format": {
                    "type": "json_schema",
                    "name": "spot_semantic_residual_v2",
                    "strict": True,
                    "schema": SCHEMA_V2,
                },
            },
            max_output_tokens=args.max_output_tokens,
            store=False,
        )
        result_rows = json.loads(response.output_text)["results"]
        expected = set(part["spot_id"].astype(int))
        actual = {int(x["spot_id"]) for x in result_rows}
        if expected != actual:
            raise RuntimeError(f"Batch {batch_idx} ID mismatch")
        for x in result_rows:
            validate_logic(x)

        in_tok = int(getattr(response.usage, "input_tokens", 0) or 0)
        out_tok = int(getattr(response.usage, "output_tokens", 0) or 0)
        cost = estimate_cost(in_tok, out_tok)

        for x in result_rows:
            novelty = x.pop("novelty")
            residual_type = x.pop("residual_type")
            x["llm_novelty"] = novelty
            x["llm_residual_type"] = residual_type
            x["llm_incremental_issue"] = novelty.startswith("residual_")
            x["llm_requires_human_review"] = (
                novelty == "residual_actionable" or x["new_rule_candidate"]
            )
            x["llm_actionability"] = (
                "human_review"
                if x["llm_requires_human_review"]
                else ("monitor" if novelty == "residual_ambiguous" else "none")
            )
            x["llm_batch_index"] = batch_idx
            x["llm_model"] = args.model
            x["llm_input_tokens_batch"] = in_tok
            x["llm_output_tokens_batch"] = out_tok
            x["llm_estimated_cost_usd_batch"] = cost
            outputs.append(x)

        usage_rows.append(
            {
                "batch_index": batch_idx,
                "n_records": len(part),
                "model": args.model,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "estimated_cost_usd": cost,
            }
        )

    llm = pd.DataFrame(outputs).rename(
        columns={
            "use_case_family": "llm_use_case_family",
            "adaptive_reuse_plausible": "llm_adaptive_reuse_plausible",
            "new_rule_candidate": "llm_new_rule_candidate",
            "confidence": "llm_confidence",
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
    print(usage.to_string(index=False))


def parse_args():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=root / "data" / "pilot_input_100.csv")
    p.add_argument("--output", type=Path, default=root / "results" / "pilot_llm_results_100_v2.csv")
    p.add_argument("--usage-output", type=Path, default=root / "results" / "pilot_usage_summary_v2.csv")
    p.add_argument("--model", default=MODEL_DEFAULT)
    p.add_argument("--batch-size", type=int, default=20)
    p.add_argument("--max-output-tokens", type=int, default=1800)
    p.add_argument("--limit", type=int, default=100)
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
