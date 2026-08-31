# LLM cache

The cache is intentionally empty in the committed Prompt-12 state.

`run_llm_audit.py --mode live` writes one JSON file per unique SHA256 of:

- model;
- prompt;
- JSON Schema;
- compact listing payload including deterministic-rule context.

A cache hit performs no new API call and contributes USD 0 new spend.

Cached model outputs are evidence, not ground truth. Do not commit API keys or secrets here.

No historical workflow artifact is copied into this directory and no synthetic LLM output is fabricated merely to populate the cache.
