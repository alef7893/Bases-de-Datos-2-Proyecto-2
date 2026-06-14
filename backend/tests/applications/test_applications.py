from pathlib import Path

import pytest

from src.applications.app04_multimodal_recommender import MultimodalRecommender
from src.applications.app01_visual_search import VisualSearch
from src.common.models import Modality, Product, SearchResult
from src.retrieval.shared.catalog import ProductCatalog
from src.retrieval.shared.fusion import WeightedScoreFusion


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.queries = []

    def search(self, query, top_k=10):
        self.queries.append(query)
        return self.results[:top_k]


def _catalog() -> ProductCatalog:
    return ProductCatalog(
        [
            Product(
                product_id=1,
                canonical_text="black shoes",
                image_path=Path("one.jpg"),
                has_image=True,
                metadata={"product_display_name": "One"},
            ),
            Product(
                product_id=2,
                canonical_text="sports shoes",
                image_path=Path("two.jpg"),
                has_image=True,
                metadata={"product_display_name": "Two"},
            ),
            Product(
                product_id=3,
                canonical_text="casual shoes",
                image_path=Path("three.jpg"),
                has_image=True,
                metadata={"product_display_name": "Three"},
            ),
        ]
    )


def test_visual_search_enriches_results() -> None:
    retriever = FakeRetriever(
        [SearchResult(product_id=2, score=0.8, rank=1, modality=Modality.IMAGE)]
    )

    results = VisualSearch(_catalog(), retriever).search(product_id=1, top_k=1)

    assert retriever.queries[0].product_id == 1
    assert results[0].metadata["product_display_name"] == "Two"


def test_visual_search_requires_one_input() -> None:
    application = VisualSearch(_catalog(), FakeRetriever([]))

    with pytest.raises(ValueError):
        application.search()
    with pytest.raises(ValueError):
        application.search(product_id=1, top_k=0)


def test_multimodal_recommender_fuses_and_enriches() -> None:
    text = FakeRetriever(
        [
            SearchResult(product_id=2, score=1.0, rank=1, modality=Modality.TEXT),
            SearchResult(product_id=3, score=0.5, rank=2, modality=Modality.TEXT),
        ]
    )
    image = FakeRetriever(
        [
            SearchResult(product_id=3, score=1.0, rank=1, modality=Modality.IMAGE),
            SearchResult(product_id=2, score=0.2, rank=2, modality=Modality.IMAGE),
        ]
    )
    application = MultimodalRecommender(
        _catalog(),
        text,
        image,
        WeightedScoreFusion({Modality.TEXT: 0.4, Modality.IMAGE: 0.6}),
    )

    results = application.recommend(product_id=1, top_k=2)

    assert [result.product_id for result in results] == [3, 2]
    assert results[0].metadata["product_display_name"] == "Three"
    assert results[0].metadata["modality_scores"]["image"] == 1.0






