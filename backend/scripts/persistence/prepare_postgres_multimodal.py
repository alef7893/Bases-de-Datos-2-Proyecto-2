"""Load multimodal artifacts and prepare PostgreSQL GIN and HNSW indexes."""

from __future__ import annotations

import argparse
import json

from src.common.config import load_project_config
from src.retrieval.postgres.image import PgvectorVisualRepository
from src.retrieval.postgres.text import PostgresTextRepository
from src.persistence.postgres_client import PostgresClient
from src.persistence.artifact_loader import ArtifactPostgresLoader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_project_config()
    scale = args.scale or config.data.active_scale
    PostgresClient(config.postgres).apply_sql_directory("sql")
    counts = ArtifactPostgresLoader(config, scale).load()
    visual_repository = PgvectorVisualRepository(config.postgres)
    visual_repository.rebuild_hnsw_index(
        scale=scale,
        m=config.phase3.hnsw_m,
        ef_construction=config.phase3.hnsw_ef_construction,
    )
    print(
        json.dumps(
            {
                "scale": scale,
                "counts": counts,
                "gin_index_size_bytes": PostgresTextRepository(
                    config.postgres
                ).index_size_bytes(),
                "hnsw_index_size_bytes": visual_repository.index_size_bytes(scale),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
