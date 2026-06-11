from src.common.models import Product
from src.multimodal.stage_01_content.partitions import select_products, split_products


def _products() -> list[Product]:
    return [
        Product(
            product_id=index,
            categories={"masterCategory": "Apparel" if index < 7 else "Footwear"},
            duplicate_image_group="duplicate" if index in (1, 2) else None,
        )
        for index in range(1, 11)
    ]


def test_selection_is_reproducible_and_keeps_duplicate_group() -> None:
    first = select_products(_products(), target_size=5, seed=42)
    second = select_products(_products(), target_size=5, seed=42)

    first_ids = {product.product_id for product in first}
    assert [product.product_id for product in first] == [
        product.product_id for product in second
    ]
    assert ({1, 2} <= first_ids) or ({1, 2}.isdisjoint(first_ids))


def test_split_keeps_duplicate_group_together() -> None:
    splits = split_products(
        _products(),
        ratios={"train": 0.8, "validation": 0.1, "test": 0.1},
        seed=42,
    )

    locations = [name for name, ids in splits.items() if 1 in ids or 2 in ids]
    assert len(locations) == 1
    assert {1, 2} <= set(splits[locations[0]])



