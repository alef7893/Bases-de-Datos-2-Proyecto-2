"""Run the multimodal related-product recommendation application."""

from __future__ import annotations

import argparse
import json

from src.applications.backend import (
    build_application_backend,
    build_application_backend_with_postgres,
)
from src.common.config import load_project_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-id", required=True, type=int)
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--engine", choices=("custom", "postgres"), default="custom")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    builder = (
        build_application_backend_with_postgres
        if args.engine == "postgres"
        else build_application_backend
    )
    backend = builder(load_project_config(), scale=args.scale)
    recommender = (
        backend.multimodal_recommender_postgres
        if args.engine == "postgres"
        else backend.multimodal_recommender
    )
    results = recommender.recommend(
        product_id=args.product_id,
        top_k=args.top_k,
    )
    print(json.dumps([result.model_dump(mode="json") for result in results], indent=2))


if __name__ == "__main__":
    main()
