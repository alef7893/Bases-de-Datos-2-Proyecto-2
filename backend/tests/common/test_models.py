import math

import pytest
from pydantic import ValidationError

from src.common.models import Modality, Product, Query, SearchResult


def test_product_normalizes_whitespace() -> None:
    product = Product(product_id=1, canonical_text="  black   sports shoes ")

    assert product.canonical_text == "black sports shoes"


def test_query_normalizes_whitespace() -> None:
    query = Query(modality=Modality.TEXT, text=" women   casual handbag ")

    assert query.text == "women casual handbag"


def test_search_result_rejects_non_finite_score() -> None:
    with pytest.raises(ValidationError):
        SearchResult(
            product_id=1,
            score=math.inf,
            rank=1,
            modality=Modality.TEXT,
        )
