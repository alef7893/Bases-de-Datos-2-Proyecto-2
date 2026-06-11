from pathlib import Path

from src.common.models import Modality, Product, SearchResult
from src.presentation.presentation import format_product_option, result_summary
from src.multimodal.stage_06_similarity_search.catalog import ProductCatalog


def test_catalog_products_are_sorted() -> None:
    catalog = ProductCatalog([Product(product_id=3), Product(product_id=1)])

    assert [product.product_id for product in catalog.products()] == [1, 3]


def test_presentation_helpers() -> None:
    product = Product(
        product_id=1,
        metadata={"product_display_name": "Black Shoes"},
        categories={"articleType": "Sports Shoes"},
    )
    result = SearchResult(
        product_id=1,
        rank=1,
        score=0.98765,
        modality=Modality.MULTIMODAL,
        metadata={
            "product_display_name": "Black Shoes",
            "image_path": str(Path("image.jpg")),
            "categories": {"articleType": "Sports Shoes", "baseColour": "Black"},
            "modality_scores": {"text": 0.9, "image": 0.8},
        },
    )

    assert format_product_option(product) == "1 | Black Shoes | Sports Shoes"
    assert result_summary(result)["score"] == 0.9877
    assert result_summary(result)["image_score"] == 0.8




