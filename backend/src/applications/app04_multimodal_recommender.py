"""Multimodal related-product recommendation application."""

from __future__ import annotations

from src.common.interfaces import Retriever
from src.common.models import Modality, Query, SearchResult
from src.retrieval.shared.catalog import ProductCatalog
from src.retrieval.shared.fusion import WeightedScoreFusion


class MultimodalRecommender:
    def __init__(
        self,
        catalog: ProductCatalog,
        text_retriever: Retriever,
        visual_retriever: Retriever,
        fusion: WeightedScoreFusion,
        candidate_multiplier: int = 5,
    ) -> None:
        if candidate_multiplier <= 0:
            raise ValueError("candidate_multiplier must be positive")
        self.catalog = catalog
        self.text_retriever = text_retriever
        self.visual_retriever = visual_retriever
        self.fusion = fusion
        self.candidate_multiplier = candidate_multiplier

    def recommend(self, product_id: int, top_k: int = 10) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        product = self.catalog.get(product_id)
        candidate_k = max(top_k, top_k * self.candidate_multiplier)
        query = Query(
            modality=Modality.MULTIMODAL,
            text=product.canonical_text,
            image_path=product.image_path,
            product_id=product_id,
        )
        text_results = self.text_retriever.search(query, top_k=candidate_k)
        visual_results = (
            self.visual_retriever.search(query, top_k=candidate_k)
            if product.image_path is not None
            else []
        )
        results = self.fusion.fuse(
            {
                Modality.TEXT: text_results,
                Modality.IMAGE: visual_results,
            },
            top_k=top_k,
        )
        return self.catalog.enrich(results)





