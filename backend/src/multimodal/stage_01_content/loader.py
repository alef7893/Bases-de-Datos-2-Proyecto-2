"""Load the Fashion Product Images Dataset into canonical Product records."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from src.common.models import Product

from .cleaner import (
    build_canonical_text,
    clean_html,
    flatten_attribute_values,
    normalize_value,
)


class FashionDatasetLoader:
    """Read dataset sources without modifying the original files."""

    CATEGORY_FIELDS = (
        "gender",
        "masterCategory",
        "subCategory",
        "articleType",
        "baseColour",
        "season",
        "year",
        "usage",
    )

    def __init__(self, dataset_root: str | Path) -> None:
        self.dataset_root = Path(dataset_root)
        self.styles_csv = self.dataset_root / "styles.csv"
        self.images_dir = self.dataset_root / "images"
        self.styles_dir = self.dataset_root / "styles"
        self._validate_structure()

    def _validate_structure(self) -> None:
        required = (self.styles_csv, self.images_dir, self.styles_dir)
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Missing dataset paths: {', '.join(missing)}")

    @staticmethod
    def _sha256(path: Path, block_size: int = 1024 * 1024) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(block_size), b""):
                digest.update(block)
        return digest.hexdigest()

    def find_duplicate_image_groups(self) -> dict[int, str]:
        """Return product_id -> SHA-256 only for byte-identical image groups."""

        by_size: dict[int, list[Path]] = defaultdict(list)
        for path in self.images_dir.glob("*.jpg"):
            by_size[path.stat().st_size].append(path)

        duplicate_groups: dict[int, str] = {}
        for candidates in by_size.values():
            if len(candidates) < 2:
                continue
            by_hash: dict[str, list[Path]] = defaultdict(list)
            for path in candidates:
                by_hash[self._sha256(path)].append(path)
            for digest, paths in by_hash.items():
                if len(paths) > 1:
                    for path in paths:
                        duplicate_groups[int(path.stem)] = digest
        return duplicate_groups

    def _load_json_metadata(self, product_id: int) -> dict[str, Any]:
        path = self.styles_dir / f"{product_id}.json"
        if not path.is_file():
            return {}
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        data = payload.get("data", {})
        return data if isinstance(data, dict) else {}

    def iter_products(
        self,
        duplicate_groups: dict[int, str] | None = None,
        limit: int | None = None,
    ) -> Iterator[Product]:
        duplicate_groups = duplicate_groups or {}
        with self.styles_csv.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = csv.DictReader(stream)
            for index, row in enumerate(rows):
                if limit is not None and index >= limit:
                    break
                product_id = int(row["id"])
                details = self._load_json_metadata(product_id)
                categories = {
                    key: normalize_value(row.get(key))
                    for key in self.CATEGORY_FIELDS
                    if normalize_value(row.get(key))
                }
                description = clean_html(
                    details.get("productDescriptors", {})
                    .get("description", {})
                    .get("value")
                )
                brand = normalize_value(details.get("brandName"))
                attributes = flatten_attribute_values(details.get("articleAttributes"))
                canonical_text = build_canonical_text(
                    [
                        row.get("productDisplayName", ""),
                        *categories.values(),
                        brand,
                        description,
                        *attributes,
                    ]
                )
                image_path = self.images_dir / f"{product_id}.jpg"
                has_image = image_path.is_file()
                yield Product(
                    product_id=product_id,
                    canonical_text=canonical_text,
                    image_path=image_path.resolve() if has_image else None,
                    categories=categories,
                    metadata={
                        "product_display_name": normalize_value(
                            row.get("productDisplayName")
                        ),
                        "brand_name": brand,
                        "description": description,
                        "article_attributes": details.get("articleAttributes", {}),
                        "json_path": str((self.styles_dir / f"{product_id}.json").resolve()),
                    },
                    has_image=has_image,
                    has_description=bool(description),
                    duplicate_image_group=duplicate_groups.get(product_id),
                )

    def write_catalog(
        self,
        output_path: str | Path,
        duplicate_groups: dict[int, str] | None = None,
        limit: int | None = None,
    ) -> int:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            for product in self.iter_products(duplicate_groups=duplicate_groups, limit=limit):
                stream.write(product.model_dump_json() + "\n")
                count += 1
        return count


def read_catalog(path: str | Path) -> Iterator[Product]:
    with Path(path).open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield Product.model_validate_json(line)
