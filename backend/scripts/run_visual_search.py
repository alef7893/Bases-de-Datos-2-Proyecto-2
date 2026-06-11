"""Run the visual e-commerce search application."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.applications.backend import build_phase2_backend
from src.common.config import load_project_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--product-id", type=int)
    group.add_argument("--image", type=Path)
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    parser.add_argument("--top-k", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backend = build_phase2_backend(load_project_config(), scale=args.scale)
    results = backend.visual_search.search(
        product_id=args.product_id,
        image_path=args.image,
        top_k=args.top_k,
    )
    print(json.dumps([result.model_dump(mode="json") for result in results], indent=2))


if __name__ == "__main__":
    main()
