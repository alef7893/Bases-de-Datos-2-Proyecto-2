import csv
import json
from pathlib import Path

from src.multimodal.stage_01_content.loader import FashionDatasetLoader, read_catalog


def _create_dataset(root: Path) -> Path:
    dataset = root / "dataset"
    (dataset / "images").mkdir(parents=True)
    (dataset / "styles").mkdir()
    with (dataset / "styles.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "id",
                "gender",
                "masterCategory",
                "subCategory",
                "articleType",
                "baseColour",
                "season",
                "year",
                "usage",
                "productDisplayName",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "id": "1",
                "gender": "Men",
                "masterCategory": "Footwear",
                "subCategory": "Shoes",
                "articleType": "Sports Shoes",
                "baseColour": "Black",
                "season": "Summer",
                "year": "2012",
                "usage": "Sports",
                "productDisplayName": "Black Sports Shoes",
            }
        )
    (dataset / "images" / "1.jpg").write_bytes(b"same-image")
    payload = {
        "data": {
            "brandName": "Example",
            "productDescriptors": {
                "description": {"value": "<p>Lightweight shoe</p>"}
            },
            "articleAttributes": {"Pattern": "Solid"},
        }
    }
    (dataset / "styles" / "1.json").write_text(json.dumps(payload), encoding="utf-8")
    return dataset


def test_loader_builds_canonical_product(tmp_path: Path) -> None:
    dataset = _create_dataset(tmp_path)
    loader = FashionDatasetLoader(dataset)

    product = next(loader.iter_products())

    assert product.product_id == 1
    assert product.has_image
    assert product.has_description
    assert "Black Sports Shoes" in product.canonical_text
    assert "Lightweight shoe" in product.canonical_text


def test_catalog_round_trip(tmp_path: Path) -> None:
    loader = FashionDatasetLoader(_create_dataset(tmp_path))
    output = tmp_path / "products.jsonl"

    assert loader.write_catalog(output) == 1
    assert list(read_catalog(output))[0].product_id == 1


def test_duplicate_image_groups_only_include_identical_files(tmp_path: Path) -> None:
    dataset = _create_dataset(tmp_path)
    (dataset / "images" / "2.jpg").write_bytes(b"same-image")
    (dataset / "images" / "3.jpg").write_bytes(b"other-data")
    loader = FashionDatasetLoader(dataset)

    groups = loader.find_duplicate_image_groups()

    assert groups[1] == groups[2]
    assert 3 not in groups



