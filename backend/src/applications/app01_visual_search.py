"""Visual e-commerce search application."""

from __future__ import annotations

from pathlib import Path

from src.common.interfaces import Retriever
from src.common.models import Modality, Query, SearchResult
from src.retrieval.shared.catalog import ProductCatalog


class VisualSearch:
    def __init__(self, catalog: ProductCatalog, retriever: Retriever) -> None:
        self.catalog = catalog
        self.retriever = retriever

    def search(
        self,
        *,
        product_id: int | None = None,
        image_path: str | Path | None = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if (product_id is None) == (image_path is None):
            raise ValueError("provide exactly one of product_id or image_path")
        if product_id is not None:
            product = self.catalog.get(product_id)
            if product.image_path is None:
                raise ValueError(f"Product has no image: {product_id}")
            image_path = product.image_path

        results = self.retriever.search(
            Query(
                modality=Modality.IMAGE,
                image_path=Path(image_path),
                product_id=product_id,
            ),
            top_k=top_k,
        )
        return self.catalog.enrich(results)





