"""Load visual artifacts into PostgreSQL and build the Phase 3 HNSW index."""

from __future__ import annotations

import argparse
import json

from src.common.config import load_project_config
from src.retrieval.postgres.image import (
    PgvectorVisualRepository,
    VisualArtifactPostgresLoader,
)
from src.persistence.postgres_client import PostgresClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    parser.add_argument("--init-schema", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_project_config()
    scale = args.scale or config.data.active_scale
    if args.init_schema:
        PostgresClient(config.postgres).apply_sql_directory("sql")
    counts = VisualArtifactPostgresLoader(config, scale).load()
    repository = PgvectorVisualRepository(config.postgres)
    repository.rebuild_hnsw_index(
        scale=scale,
        m=config.phase3.hnsw_m,
        ef_construction=config.phase3.hnsw_ef_construction,
    )
    print(
        json.dumps(
            {
                "scale": scale,
                "counts": counts,
                "hnsw_index_size_bytes": repository.index_size_bytes(scale),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
