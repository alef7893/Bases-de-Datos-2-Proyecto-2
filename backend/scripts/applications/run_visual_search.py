"""Run the visual e-commerce search application."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.applications.backend import build_application_backend, build_application_backend_with_hnsw
from src.common.config import load_project_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--product-id", type=int)
    group.add_argument("--image", type=Path)
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--engine", choices=("custom", "hnsw"), default="custom")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_project_config()
    backend = (
        build_application_backend_with_hnsw(config, scale=args.scale)
        if args.engine == "hnsw"
        else build_application_backend(config, scale=args.scale)
    )
    application = (
        backend.visual_search_hnsw if args.engine == "hnsw" else backend.visual_search
    )
    results = application.search(
        product_id=args.product_id,
        image_path=args.image,
        top_k=args.top_k,
    )
    print(json.dumps([result.model_dump(mode="json") for result in results], indent=2))


if __name__ == "__main__":
    main()

