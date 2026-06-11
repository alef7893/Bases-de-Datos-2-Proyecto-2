"""Query the custom visual inverted index using SIFT visual words."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from src.common.models import Modality, Query, SearchResult
from src.multimodal.stage_04_codebook.visual_codebook import VisualCodebook
from src.multimodal.stage_04_codebook.visual_histogram import build_visual_histogram, sparse_visual_histogram
from src.multimodal.stage_03_extractor_features.sift_extractor import SIFTExtractor


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

        descriptors = self.extractor.extract_path(query.image_path)
        assignments = self.codebook.transform(descriptors)
        query_histogram = sparse_visual_histogram(
            build_visual_histogram(assignments, self.codebook.size)
        )
        scores: dict[int, float] = defaultdict(float)
        for word_id, query_weight in query_histogram.items():
            for product_id, product_weight in self.postings.get(word_id, []):
                product_id = int(product_id)
                if product_id != query.product_id:
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



