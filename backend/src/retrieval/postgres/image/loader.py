"""Load only the visual artifacts required by the Phase 3 HNSW comparison."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from psycopg.types.json import Jsonb

from src.common.config import ProjectConfig
from src.pipeline.catalog.loader import read_catalog
from src.pipeline.image.codebook import VisualCodebook
from src.persistence.postgres_client import PostgresClient


class VisualArtifactPostgresLoader:
    TABLES = ("products", "dataset_memberships", "codebooks", "codebook_entries", "histograms")

    def __init__(self, config: ProjectConfig, scale: str) -> None:
        self.config = config
        self.scale = scale
        self.client = PostgresClient(config.postgres)
        self.artifacts = config.paths.artifacts_dir
        self.manifest = json.loads(
            (self.artifacts / "partitions" / f"{scale}.json").read_text(encoding="utf-8")
        )
        self.split_by_product = {
            int(product_id): split
            for split, product_ids in self.manifest["splits"].items()
            for product_id in product_ids
        }

    def load(self) -> dict[str, int]:
        products = [
            product
            for product in read_catalog(self.artifacts / "catalog" / "products.jsonl")
            if product.product_id in self.split_by_product and product.has_image
        ]
        vision_dir = self.artifacts / "vision" / self.scale
        codebook = VisualCodebook.load(vision_dir / "codebook.joblib")
        codebook_id = f"image-{self.scale}"

        with self.client.connect() as connection:
            self.client.execute_many(
                connection,
                """
                INSERT INTO products (
                    product_id, canonical_text, image_path, categories, metadata,
                    has_image, has_description, duplicate_image_group
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    canonical_text = EXCLUDED.canonical_text,
                    image_path = EXCLUDED.image_path,
                    categories = EXCLUDED.categories,
                    metadata = EXCLUDED.metadata,
                    has_image = EXCLUDED.has_image,
                    has_description = EXCLUDED.has_description,
                    duplicate_image_group = EXCLUDED.duplicate_image_group
                """,
                (
                    (
                        product.product_id,
                        product.canonical_text,
                        str(product.image_path),
                        Jsonb(product.categories),
                        Jsonb(product.metadata),
                        product.has_image,
                        product.has_description,
                        product.duplicate_image_group,
                    )
                    for product in products
                ),
            )
            self.client.execute_many(
                connection,
                """
                INSERT INTO dataset_memberships (scale, split, product_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (scale, product_id) DO UPDATE SET split = EXCLUDED.split
                """,
                (
                    (self.scale, self.split_by_product[product.product_id], product.product_id)
                    for product in products
                ),
            )
            self.client.execute_many(
                connection,
                """
                INSERT INTO codebooks (
                    codebook_id, modality, scale, size, artifact_path, parameters
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (codebook_id) DO UPDATE SET
                    size = EXCLUDED.size,
                    artifact_path = EXCLUDED.artifact_path,
                    parameters = EXCLUDED.parameters
                """,
                [
                    (
                        codebook_id,
                        "image",
                        self.scale,
                        codebook.size,
                        str(vision_dir / "codebook.joblib"),
                        Jsonb(self.config.vision.model_dump()),
                    )
                ],
            )
            self.client.execute_many(
                connection,
                """
                INSERT INTO codebook_entries (codebook_id, codeword_id, metadata, centroid)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (codebook_id, codeword_id) DO UPDATE SET
                    metadata = EXCLUDED.metadata,
                    centroid = EXCLUDED.centroid
                """,
                (
                    (
                        codebook_id,
                        str(index),
                        Jsonb({"position": index}),
                        centroid,
                    )
                    for index, centroid in enumerate(
                        codebook.model.cluster_centers_.astype(np.float32)
                    )
                ),
            )
            self.client.execute_many(
                connection,
                """
                INSERT INTO histograms (
                    histogram_id, product_id, chunk_id, modality, scale,
                    codebook_id, sparse_values, visual_vector
                ) VALUES (%s, %s, NULL, 'image', %s, %s, %s, %s)
                ON CONFLICT (histogram_id) DO UPDATE SET
                    sparse_values = EXCLUDED.sparse_values,
                    visual_vector = EXCLUDED.visual_vector
                """,
                (
                    self._histogram_row(product.product_id, vision_dir, codebook_id)
                    for product in products
                ),
            )
            connection.commit()
        return self.client.fetch_counts(self.TABLES)

    def _histogram_row(
        self,
        product_id: int,
        vision_dir,
        codebook_id: str,
    ) -> tuple[Any, ...]:
        histogram = np.load(
            vision_dir / "histograms" / f"{product_id}.npy",
            allow_pickle=False,
        )
        sparse = {
            str(index): float(histogram[index])
            for index in np.flatnonzero(histogram)
        }
        return (
            f"image:{self.scale}:{product_id}",
            product_id,
            self.scale,
            codebook_id,
            Jsonb(sparse),
            histogram,
        )


