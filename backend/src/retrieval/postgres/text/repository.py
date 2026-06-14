"""PostgreSQL full-text search operations for product text."""

from __future__ import annotations

from src.common.config import PostgresConfig
from src.persistence.postgres_client import PostgresClient


class PostgresTextRepository:
    INDEX_NAME = "products_search_vector_gin_idx"

    def __init__(self, config: PostgresConfig) -> None:
        self.client = PostgresClient(config)

    def search(
        self,
        text: str,
        *,
        scale: str,
        top_k: int,
        exclude_product_id: int | None = None,
    ) -> list[tuple[int, float]]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if not text.strip():
            return []

        with self.client.connect(register_vector_type=False) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    WITH query AS (
                        SELECT websearch_to_tsquery(
                            'english'::regconfig,
                            regexp_replace(trim(%s), '\\s+', ' OR ', 'g')
                        ) AS value
                    )
                    SELECT products.product_id,
                           ts_rank_cd(products.search_vector, query.value) AS score
                    FROM products
                    JOIN dataset_memberships
                      ON dataset_memberships.product_id = products.product_id
                    CROSS JOIN query
                    WHERE dataset_memberships.scale = %s
                      AND products.search_vector @@ query.value
                      AND (%s::bigint IS NULL OR products.product_id <> %s)
                    ORDER BY score DESC, products.product_id
                    LIMIT %s
                    """,
                    (text, scale, exclude_product_id, exclude_product_id, top_k),
                )
                return [
                    (int(product_id), float(score))
                    for product_id, score in cursor.fetchall()
                ]

    def index_size_bytes(self) -> int:
        with self.client.connect(register_vector_type=False) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_relation_size(to_regclass(%s))",
                    (self.INDEX_NAME,),
                )
                value = cursor.fetchone()[0]
                return int(value or 0)

    def explain_search(self, text: str, *, scale: str, top_k: int) -> dict:
        with self.client.connect(register_vector_type=False) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                    WITH query AS (
                        SELECT websearch_to_tsquery(
                            'english'::regconfig,
                            regexp_replace(trim(%s), '\\s+', ' OR ', 'g')
                        ) AS value
                    )
                    SELECT products.product_id
                    FROM products
                    JOIN dataset_memberships
                      ON dataset_memberships.product_id = products.product_id
                    CROSS JOIN query
                    WHERE dataset_memberships.scale = %s
                      AND products.search_vector @@ query.value
                    ORDER BY ts_rank_cd(products.search_vector, query.value) DESC
                    LIMIT %s
                    """,
                    (text, scale, top_k),
                )
                return cursor.fetchone()[0][0]
