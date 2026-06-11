"""In-memory product catalog used by application services."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from pathlib import Path

from src.common.models import Product, SearchResult
from src.multimodal.stage_01_content.loader import read_catalog


class ProductCatalog:
    def __init__(self, products: Iterable[Product]) -> None:
        self._products = {product.product_id: product for product in products}

    @classmethod
    def from_artifacts(
        cls,
        catalog_path: str | Path,
        manifest_path: str | Path | None = None,
    ) -> "ProductCatalog":
        selected_ids: set[int] | None = None
        if manifest_path is not None:
            manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
            selected_ids = set().union(*manifest["splits"].values())
        return cls(
            product
            for product in read_catalog(catalog_path)
            if selected_ids is None or product.product_id in selected_ids
        )

    def get(self, product_id: int) -> Product:
        try:
            return self._products[product_id]
        except KeyError as error:
            raise KeyError(f"Product is not available in the active catalog: {product_id}") from error

    def products(self) -> list[Product]:
        """Devuelve los productos disponibles ordenados por identificador."""

        return sorted(self._products.values(), key=lambda product: product.product_id)

    def enrich(self, results: Sequence[SearchResult]) -> list[SearchResult]:
        enriched: list[SearchResult] = []
        for result in results:
            product = self.get(result.product_id)
            metadata = dict(result.metadata)
            metadata.update(
                {
                    "product_display_name": product.metadata.get(
                        "product_display_name", ""
                    ),
                    "image_path": str(product.image_path) if product.image_path else None,
                    "categories": product.categories,
                }
            )
            enriched.append(result.model_copy(update={"metadata": metadata}))
        return enriched

    def __len__(self) -> int:
        return len(self._products)



