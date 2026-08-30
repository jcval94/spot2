from __future__ import annotations

from collections import Counter
from pathlib import Path

from .io_utils import load_inventory, write_csv, write_json


def run(output_dir: Path) -> dict:
    rows = load_inventory()
    descriptions = [(row.get("description") or "").strip() for row in rows]
    desc_counts = Counter(descriptions)

    sentences: list[str] = []
    for description in descriptions:
        sentences.extend(part.strip() for part in description.split(".") if part.strip())
    sentence_counts = Counter(sentences)

    repeated_rows = sum(1 for description in descriptions if desc_counts[description] > 1)
    summary = {
        "n_spots": len(rows),
        "unique_exact_descriptions": len(desc_counts),
        "exact_description_uniqueness_rate": len(desc_counts) / len(rows),
        "share_rows_with_repeated_exact_description": repeated_rows / len(rows),
        "unique_description_sentences": len(sentence_counts),
    }
    write_json(output_dir / "copy_profile_summary.json", summary)

    top = [
        {"sentence": sentence, "count": count, "share_of_spots": count / len(rows)}
        for sentence, count in sentence_counts.most_common()
    ]
    write_csv(
        output_dir / "description_sentence_counts.csv",
        top,
        ["sentence", "count", "share_of_spots"],
    )
    return summary
