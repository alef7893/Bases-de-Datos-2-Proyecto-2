"""Load Phase 2 artifacts into PostgreSQL idempotently."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from psycopg.types.json import Jsonb

from src.common.config import ProjectConfig
from src.pipeline.catalog.loader import read_catalog
from src.persistence.postgres_client import PostgresClient
from src.pipeline.text.codebook import TextCodebook
from src.pipeline.text.splitter import TextSplitter
from src.pipeline.image.codebook import VisualCodebook


class ArtifactPostgresLoader:
    TABLES = (
        "products",
        "dataset_memberships",
        "chunks",
        "codebooks",
        "codebook_entries",
        "histograms",
        "postings",
        "experiment_runs",
    )

    def __init__(self, config: ProjectConfig, scale: str) -> None:
        self.config = config
        self.scale = scale
        self.client = PostgresClient(config.postgres)
        self.artifacts = config.paths.artifacts_dir
        self.manifest = json.loads(
            (self.artifacts / "partitions" / f"{scale}.json").read_text(
                encoding="utf-8"
            )
        )
        self.split_by_product = {
            int(product_id): split
            for split, product_ids in self.manifest["splits"].items()
            for product_id in product_ids
        }

    @property
    def selected_ids(self) -> set[int]:
        return set(self.split_by_product)

    def _products(self) -> list[Any]:
        return [
            product
            for product in read_catalog(self.artifacts / "catalog" / "products.jsonl")
            if product.product_id in self.selected_ids
        ]

    def _text_postings(self) -> tuple[list[tuple[Any, ...]], dict[str, dict[str, float]]]:
        rows: list[tuple[Any, ...]] = []
        histograms: dict[str, dict[str, float]] = defaultdict(dict)
        path = self.artifacts / "text" / self.scale / "index" / "postings.jsonl"
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                payload = json.loads(line)
                term = payload["term"]
                for chunk_id, product_id, weight in payload["postings"]:
                    rows.append(
                        ("text", self.scale, term, chunk_id, int(product_id), float(weight))
                    )
                    histograms[str(chunk_id)][term] = float(weight)
        return rows, histograms

    def _visual_postings(self) -> list[tuple[Any, ...]]:
        rows: list[tuple[Any, ...]] = []
        path = self.artifacts / "vision" / self.scale / "index" / "postings.jsonl"
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                payload = json.loads(line)
                word_id = str(payload["word_id"])
                for product_id, weight in payload["postings"]:
                    rows.append(
                        (
                            "image",
                            self.scale,
                            word_id,
                            str(product_id),
                            int(product_id),
                            float(weight),
                        )
                    )
        return rows

    def load(self, run_id: str | None = None) -> dict[str, int]:
        run_id = run_id or f"phase2-load-{self.scale}"
        products = self._products()
        text_dir = self.artifacts / "text" / self.scale
        vision_dir = self.artifacts / "vision" / self.scale
        text_codebook = TextCodebook.load(text_dir / "codebook.json")
        text_postings, text_histograms = self._text_postings()
        visual_postings = self._visual_postings()
        product_by_id = {product.product_id: product for product in products}

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
                        str(product.image_path) if product.image_path else None,
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
                    (self.scale, split, product_id)
                    for product_id, split in self.split_by_product.items()
                ),
            )

            splitter = TextSplitter(
                max_tokens=self.config.text.chunk_max_tokens,
                overlap_tokens=self.config.text.chunk_overlap_tokens,
            )
            chunk_rows: list[tuple[Any, ...]] = []
            for product in products:
                for chunk in splitter.split(product):
                    chunk_rows.append(
                        (
                            chunk.chunk_id,
                            chunk.product_id,
                            "text",
                            chunk.position,
                            chunk.content,
                            Jsonb(chunk.metadata),
                        )
                    )
            self.client.execute_many(
                connection,
                """
                INSERT INTO chunks (chunk_id, product_id, modality, position, content, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    product_id = EXCLUDED.product_id,
                    modality = EXCLUDED.modality,
                    position = EXCLUDED.position,
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata
                """,
                chunk_rows,
            )

            text_codebook_id = f"text-{self.scale}"
            visual_codebook_id = f"image-{self.scale}"
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
                        text_codebook_id,
                        "text",
                        self.scale,
                        len(text_codebook.terms),
                        str(text_dir / "codebook.json"),
                        Jsonb(self.config.text.model_dump()),
                    ),
                    (
                        visual_codebook_id,
                        "image",
                        self.scale,
                        self.config.vision.codebook_size,
                        str(vision_dir / "codebook.joblib"),
                        Jsonb(self.config.vision.model_dump()),
                    ),
                ],
            )
            visual_codebook = VisualCodebook.load(vision_dir / "codebook.joblib")
            self.client.execute_many(
                connection,
                """
                INSERT INTO codebook_entries (
                    codebook_id, codeword_id, metadata, centroid
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (codebook_id, codeword_id) DO UPDATE SET
                    metadata = EXCLUDED.metadata,
                    centroid = EXCLUDED.centroid
                """,
                (
                    (
                        text_codebook_id,
                        term,
                        Jsonb({"idf": text_codebook.idf[term], "position": position}),
                        None,
                    )
                    for position, term in enumerate(text_codebook.terms)
                ),
            )
            self.client.execute_many(
                connection,
                """
                INSERT INTO codebook_entries (
                    codebook_id, codeword_id, metadata, centroid
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (codebook_id, codeword_id) DO UPDATE SET
                    metadata = EXCLUDED.metadata,
                    centroid = EXCLUDED.centroid
                """,
                (
                    (
                        visual_codebook_id,
                        str(index),
                        Jsonb({"position": index}),
                        centroid,
                    )
                    for index, centroid in enumerate(
                        visual_codebook.model.cluster_centers_.astype(np.float32)
                    )
                ),
            )

            self.client.execute_many(
                connection,
                """
                INSERT INTO histograms (
                    histogram_id, product_id, chunk_id, modality, scale,
                    codebook_id, sparse_values, visual_vector
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (histogram_id) DO UPDATE SET
                    sparse_values = EXCLUDED.sparse_values,
                    visual_vector = EXCLUDED.visual_vector
                """,
                (
                    (
                        f"text:{self.scale}:{chunk_id}",
                        product_by_id[int(chunk_id.split(":")[1])].product_id,
                        chunk_id,
                        "text",
                        self.scale,
                        text_codebook_id,
                        Jsonb(values),
                        None,
                    )
                    for chunk_id, values in text_histograms.items()
                ),
            )
            self.client.execute_many(
                connection,
                """
                INSERT INTO histograms (
                    histogram_id, product_id, chunk_id, modality, scale,
                    codebook_id, sparse_values, visual_vector
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (histogram_id) DO UPDATE SET
                    sparse_values = EXCLUDED.sparse_values,
                    visual_vector = EXCLUDED.visual_vector
                """,
                (
                    (
                        f"image:{self.scale}:{product.product_id}",
                        product.product_id,
                        None,
                        "image",
                        self.scale,
                        visual_codebook_id,
                        Jsonb(
                            {
                                str(index): float(histogram[index])
                                for index in np.flatnonzero(histogram)
                            }
                        ),
                        histogram,
                    )
                    for product in products
                    if product.has_image
                    for histogram in [
                        np.load(
                            vision_dir / "histograms" / f"{product.product_id}.npy",
                            allow_pickle=False,
                        )
                    ]
                ),
            )

            self.client.execute_many(
                connection,
                """
                INSERT INTO postings (
                    modality, scale, codeword_id, item_id, product_id, weight
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (modality, scale, codeword_id, item_id)
                DO UPDATE SET weight = EXCLUDED.weight, product_id = EXCLUDED.product_id
                """,
                text_postings,
            )
            self.client.execute_many(
                connection,
                """
                INSERT INTO postings (
                    modality, scale, codeword_id, item_id, product_id, weight
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (modality, scale, codeword_id, item_id)
                DO UPDATE SET weight = EXCLUDED.weight, product_id = EXCLUDED.product_id
                """,
                visual_postings,
            )
            self.client.execute_many(
                connection,
                """
                INSERT INTO experiment_runs (
                    run_id, name, scale, seed, status, parameters, metrics, completed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (run_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    parameters = EXCLUDED.parameters,
                    metrics = EXCLUDED.metrics,
                    completed_at = now()
                """,
                [
                    (
                        run_id,
                        "phase2-artifact-load",
                        self.scale,
                        self.config.project.seed,
                        "completed",
                        Jsonb(
                            {
                                "text": self.config.text.model_dump(),
                                "vision": self.config.vision.model_dump(),
                            }
                        ),
                        Jsonb(
                            {
                                "products": len(products),
                                "text_postings": len(text_postings),
                                "visual_postings": len(visual_postings),
                            }
                        ),
                    )
                ],
            )
            connection.commit()
        return self.client.fetch_counts(self.TABLES)





