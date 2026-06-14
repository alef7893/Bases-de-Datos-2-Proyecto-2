"""Query the custom SPIMI text index and aggregate chunks by product."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from src.common.models import Modality, Query, SearchResult
from src.pipeline.text.codebook import TextCodebook
from src.pipeline.text.extractor import TextFeatureExtractor


class TextRetriever:
    def __init__(
        self,
        index_dir: str | Path,
        codebook: TextCodebook,
        extractor: TextFeatureExtractor,
    ) -> None:
        self.index_dir = Path(index_dir)
        self.codebook = codebook
        self.extractor = extractor
        self.postings = self._load_postings(self.index_dir / "postings.jsonl")

    @staticmethod
    def _load_postings(path: Path) -> dict[str, list[list[object]]]:
        postings: dict[str, list[list[object]]] = {}
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                payload = json.loads(line)
                postings[payload["term"]] = payload["postings"]
        return postings

    def search(self, query: Query, top_k: int = 10) -> list[SearchResult]:
        if query.modality not in {Modality.TEXT, Modality.MULTIMODAL}:
            raise ValueError("TextRetriever only accepts text or multimodal queries")
        if not query.text:
            return []

        tokens = self.extractor.extract_text(query.text)
        query_vector = self.codebook.transform(tokens)
        chunk_scores: dict[str, float] = defaultdict(float)
        chunk_products: dict[str, int] = {}
        for term, query_weight in query_vector.items():
            for chunk_id, product_id, document_weight in self.postings.get(term, []):
                chunk_scores[str(chunk_id)] += query_weight * float(document_weight)
                chunk_products[str(chunk_id)] = int(product_id)

        product_scores: dict[int, tuple[float, str]] = {}
        for chunk_id, score in chunk_scores.items():
            product_id = chunk_products[chunk_id]
            if product_id == query.product_id:
                continue
            current = product_scores.get(product_id)
            if current is None or score > current[0]:
                product_scores[product_id] = (score, chunk_id)

        ranked = sorted(product_scores.items(), key=lambda item: (-item[1][0], item[0]))
        return [
            SearchResult(
                product_id=product_id,
                score=score,
                rank=rank,
                modality=Modality.TEXT,
                metadata={"best_chunk_id": chunk_id},
            )
            for rank, (product_id, (score, chunk_id)) in enumerate(
                ranked[:top_k], start=1
            )
        ]





