"""Initialize PostgreSQL and load Phase 2 artifacts."""

from __future__ import annotations

import argparse
import json

from src.common.config import load_project_config
from src.persistence.postgres_client import PostgresClient
from src.persistence.postgres_loader import ArtifactPostgresLoader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    parser.add_argument("--init-schema", action="store_true")
    parser.add_argument("--counts-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_project_config()
    scale = args.scale or config.data.active_scale
    client = PostgresClient(config.postgres)
    if args.init_schema:
        client.apply_sql_directory("sql")
    if args.counts_only:
        counts = client.fetch_counts(ArtifactPostgresLoader.TABLES)
    else:
        counts = ArtifactPostgresLoader(config, scale).load()
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
