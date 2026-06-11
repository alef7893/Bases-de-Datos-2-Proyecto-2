"""Inverted index for normalized visual-word histograms."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path


class VisualInvertedIndexer:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def build(
        self, histograms: Iterable[tuple[int, Mapping[int, float]]]
    ) -> dict[str, int]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        postings: dict[int, list[list[float | int]]] = defaultdict(list)
        product_count = 0
        nonzero_count = 0
        for product_id, histogram in histograms:
            product_count += 1
            for word_id, weight in histogram.items():
                postings[word_id].append([product_id, weight])
                nonzero_count += 1

        path = self.output_dir / "postings.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            for word_id in sorted(postings):
                values = sorted(postings[word_id], key=lambda item: int(item[0]))
                stream.write(
                    json.dumps({"word_id": word_id, "postings": values}) + "\n"
                )

        summary = {
            "products": product_count,
            "visual_words": len(postings),
            "nonzero_postings": nonzero_count,
        }
        (self.output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        return summary
