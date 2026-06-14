"""PostgreSQL vector search operations for visual histograms."""

from __future__ import annotations

from typing import Literal

import numpy as np
from psycopg import sql

from src.common.config import PostgresConfig
from src.persistence.postgres_client import PostgresClient


class PgvectorVisualRepository:
    VALID_SCALES = {"1k", "10k", "full"}

    def __init__(self, config: PostgresConfig) -> None:
        self.client = PostgresClient(config)

    def search(
        self,
        histogram: np.ndarray,
        *,
        scale: str,
        top_k: int,
        exclude_product_id: int | None = None,
        method: Literal["hnsw", "exact"] = "hnsw",
        ef_search: int = 100,
    ) -> list[tuple[int, float]]:
        if top_k <= 0 or ef_search <= 0:
            raise ValueError("top_k and ef_search must be positive")
        if method not in {"hnsw", "exact"}:
            raise ValueError(f"Unsupported search method: {method}")
        self._index_name(scale)

        with self.client.connect() as connection:
            with connection.cursor() as cursor:
                if method == "hnsw":
                    cursor.execute(
                        "SELECT set_config('hnsw.ef_search', %s, true)",
                        (str(ef_search),),
                    )
                    cursor.execute("SET LOCAL enable_seqscan = off")
                else:
                    cursor.execute("SET LOCAL enable_indexscan = off")
                    cursor.execute("SET LOCAL enable_bitmapscan = off")

                cursor.execute(
                    sql.SQL(
                        """
                    SELECT product_id, 1 - (visual_vector <=> %s) AS score
                    FROM histograms
                    WHERE modality = 'image'
                      AND scale = {}
                      AND visual_vector IS NOT NULL
                      AND (%s::bigint IS NULL OR product_id <> %s)
                    ORDER BY visual_vector <=> %s
                    LIMIT %s
                    """
                    ).format(sql.Literal(scale)),
                    (
                        histogram,
                        exclude_product_id,
                        exclude_product_id,
                        histogram,
                        top_k,
                    ),
                )
                return [
                    (int(product_id), float(score))
                    for product_id, score in cursor.fetchall()
                ]

    def rebuild_hnsw_index(
        self,
        *,
        scale: str,
        m: int = 16,
        ef_construction: int = 64,
    ) -> None:
        if m <= 0 or ef_construction <= 0:
            raise ValueError("HNSW parameters must be positive")
        index_name = self._index_name(scale)
        with self.client.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP INDEX IF EXISTS {}").format(
                        sql.Identifier(index_name)
                    )
                )
                cursor.execute(
                    sql.SQL(
                        """
                        CREATE INDEX {} ON histograms
                        USING hnsw (visual_vector vector_cosine_ops)
                        WITH (m = {}, ef_construction = {})
                        WHERE modality = 'image' AND visual_vector IS NOT NULL
                          AND scale = {}
                        """
                    ).format(
                        sql.Identifier(index_name),
                        sql.Literal(m),
                        sql.Literal(ef_construction),
                        sql.Literal(scale),
                    )
                )
            connection.commit()

    def index_size_bytes(self, scale: str) -> int:
        index_name = self._index_name(scale)
        with self.client.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_relation_size(to_regclass(%s))",
                    (index_name,),
                )
                value = cursor.fetchone()[0]
                return int(value or 0)

    def explain_search(
        self,
        histogram: np.ndarray,
        *,
        scale: str,
        top_k: int,
        method: Literal["hnsw", "exact"],
    ) -> dict:
        self._index_name(scale)
        with self.client.connect() as connection:
            with connection.cursor() as cursor:
                if method == "hnsw":
                    cursor.execute("SET LOCAL enable_seqscan = off")
                else:
                    cursor.execute("SET LOCAL enable_indexscan = off")
                    cursor.execute("SET LOCAL enable_bitmapscan = off")
                cursor.execute(
                    sql.SQL(
                        """
                        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                        SELECT product_id
                        FROM histograms
                        WHERE modality = 'image'
                          AND scale = {}
                          AND visual_vector IS NOT NULL
                        ORDER BY visual_vector <=> %s
                        LIMIT %s
                        """
                    ).format(sql.Literal(scale)),
                    (histogram, top_k),
                )
                return cursor.fetchone()[0][0]

    @classmethod
    def _index_name(cls, scale: str) -> str:
        if scale not in cls.VALID_SCALES:
            raise ValueError(f"Unsupported scale: {scale}")
        return f"histograms_visual_vector_hnsw_{scale}_idx"
