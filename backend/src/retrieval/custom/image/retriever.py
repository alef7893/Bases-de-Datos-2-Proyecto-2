"""Query the custom visual inverted index using SIFT visual words."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from src.common.models import Modality, Query, SearchResult
from src.pipeline.image.codebook import VisualCodebook
from src.pipeline.image.encoder import VisualHistogramEncoder
from src.pipeline.image.histogram import sparse_visual_histogram
from src.pipeline.image.sift_extractor import SIFTExtractor


class VisualRetriever:
    def __init__(
        self,
        index_dir: str | Path,
        codebook: VisualCodebook,
        extractor: SIFTExtractor,
    ) -> None:
        self.index_dir = Path(index_dir)
        self.codebook = codebook
        self.extractor = extractor
        self.encoder = VisualHistogramEncoder(codebook, extractor)
        self.postings = self._load_postings(self.index_dir / "postings.jsonl")

    @staticmethod
    def _load_postings(path: Path) -> dict[int, list[list[float | int]]]:
        postings: dict[int, list[list[float | int]]] = {}
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                payload = json.loads(line)
                postings[int(payload["word_id"])] = payload["postings"]
        return postings

    def search(self, query: Query, top_k: int = 10) -> list[SearchResult]:
        if query.modality not in {Modality.IMAGE, Modality.MULTIMODAL}:
            raise ValueError("VisualRetriever only accepts image or multimodal queries")
        if query.image_path is None:
            return []

        return self.search_histogram(
            self.encoder.encode_path(query.image_path),
            top_k=top_k,
            exclude_product_id=query.product_id,
        )

    def search_histogram(
        self,
        histogram,
        *,
        top_k: int = 10,
        exclude_product_id: int | None = None,
    ) -> list[SearchResult]:
        query_histogram = sparse_visual_histogram(histogram)
        scores: dict[int, float] = defaultdict(float)
        for word_id, query_weight in query_histogram.items():
            for product_id, product_weight in self.postings.get(word_id, []):
                product_id = int(product_id)
                if product_id != exclude_product_id:
                    scores[product_id] += query_weight * float(product_weight)

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return [
            SearchResult(
                product_id=product_id,
                score=score,
                rank=rank,
                modality=Modality.IMAGE,
            )
            for rank, (product_id, score) in enumerate(ranked[:top_k], start=1)
        ]





