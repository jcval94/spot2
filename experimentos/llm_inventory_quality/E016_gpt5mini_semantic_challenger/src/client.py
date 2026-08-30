from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[2]
E015 = ROOT / "E015_llm_inventory_semantic_audit"
PROMPT_PATH = E015 / "prompts" / "system_prompt.md"
SCHEMA_PATH = E015 / "schema" / "audit_response.schema.json"


def api_key() -> str:
    value = (
        os.getenv("OPENAIKEY")
        or os.getenv("OPENAIAPI")
        or os.getenv("OPENAI_API_KEY")
    )
    if not value:
        raise RuntimeError("Missing OPENAIKEY, OPENAIAPI, or OPENAI_API_KEY.")
    return value


def load_prompt_schema() -> tuple[str, dict[str, Any]]:
    return (
        PROMPT_PATH.read_text(encoding="utf-8"),
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8")),
    )


def audit(payload: dict[str, Any], model: str = "gpt-5-mini") -> dict[str, Any]:
    prompt, schema = load_prompt_schema()
    client = OpenAI(api_key=api_key(), max_retries=0, timeout=60.0)

    started = time.perf_counter()
    response = client.responses.create(
        model=model,
        instructions=prompt,
        input=json.dumps(payload, ensure_ascii=False),
        text={
            "format": {
                "type": "json_schema",
                "name": "inventory_semantic_audit",
                "schema": schema,
                "strict": True
            }
        },
        reasoning={"effort": "minimal"},
        max_output_tokens=1600,
        store=False
    )
    latency_ms = (time.perf_counter() - started) * 1000

    if getattr(response, "status", None) == "incomplete":
        raise RuntimeError(
            f"Incomplete response: {getattr(response, 'incomplete_details', None)}"
        )
    if not response.output_text:
        raise RuntimeError("OpenAI response did not contain output_text.")

    usage = getattr(response, "usage", None)
    return {
        "status": "ok",
        "response_id": getattr(response, "id", None),
        "model": model,
        "latency_ms": latency_ms,
        "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
        "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        "audit": json.loads(response.output_text)
    }
