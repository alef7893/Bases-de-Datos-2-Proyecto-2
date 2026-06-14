"""Retriever adapter for PostgreSQL GIN full-text search."""

from __future__ import annotations

from src.common.models import Modality, Query, SearchResult

from .repository import PostgresTextRepository


class PostgresGINTextRetriever:
    def __init__(self, repository: PostgresTextRepository, scale: str) -> None:
        self.repository = repository
        self.scale = scale

    def search(self, query: Query, top_k: int = 10) -> list[SearchResult]:
        if query.modality not in {Modality.TEXT, Modality.MULTIMODAL}:
            raise ValueError("PostgresGINTextRetriever only accepts text queries")
        if not query.text:
            return []

        rows = self.repository.search(
            query.text,
            scale=self.scale,
            top_k=top_k,
            exclude_product_id=query.product_id,
        )
        return [
            SearchResult(
                product_id=product_id,
                score=score,
                rank=rank,
                modality=Modality.TEXT,
                metadata={"engine": "postgres_gin"},
            )
            for rank, (product_id, score) in enumerate(rows, start=1)
        ]
