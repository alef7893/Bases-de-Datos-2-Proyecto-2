"""Retriever adapter for PostgreSQL pgvector HNSW."""

from __future__ import annotations

from src.common.models import Modality, Query, SearchResult
from src.pipeline.image.encoder import VisualHistogramEncoder

from .repository import PgvectorVisualRepository


class PgvectorHNSWRetriever:
    def __init__(
        self,
        repository: PgvectorVisualRepository,
        encoder: VisualHistogramEncoder,
        scale: str,
        ef_search: int = 100,
    ) -> None:
        self.repository = repository
        self.encoder = encoder
        self.scale = scale
        self.ef_search = ef_search

    def search(self, query: Query, top_k: int = 10) -> list[SearchResult]:
        if query.modality not in {Modality.IMAGE, Modality.MULTIMODAL}:
            raise ValueError("PgvectorHNSWRetriever only accepts image queries")
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
        method: str = "hnsw",
    ) -> list[SearchResult]:
        rows = self.repository.search(
            histogram,
            scale=self.scale,
            top_k=top_k,
            exclude_product_id=exclude_product_id,
            method=method,
            ef_search=self.ef_search,
        )
        return [
            SearchResult(
                product_id=product_id,
                score=score,
                rank=rank,
                modality=Modality.IMAGE,
                metadata={"engine": f"pgvector_{method}"},
            )
            for rank, (product_id, score) in enumerate(rows, start=1)
        ]


