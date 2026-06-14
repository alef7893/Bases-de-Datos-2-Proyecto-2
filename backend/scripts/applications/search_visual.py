"""Search the custom visual index from an image path or product ID."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.common.config import load_project_config
from src.common.models import Modality, Query
from src.pipeline.catalog.loader import read_catalog
from src.retrieval.custom.image.retriever import VisualRetriever
from src.pipeline.image.codebook import VisualCodebook
from src.pipeline.image.sift_extractor import SIFTExtractor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", type=Path)
    group.add_argument("--product-id", type=int)
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    parser.add_argument("--top-k", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_project_config()
    scale = args.scale or config.data.active_scale
    image_path = args.image
    if args.product_id is not None:
        product = next(
            product
            for product in read_catalog(
                config.paths.artifacts_dir / "catalog" / "products.jsonl"
            )
            if product.product_id == args.product_id
        )
        image_path = product.image_path

    output_dir = config.paths.artifacts_dir / "vision" / scale
    retriever = VisualRetriever(
        output_dir / "index",
        VisualCodebook.load(output_dir / "codebook.joblib"),
        SIFTExtractor(
            max_width=config.vision.max_image_width,
            max_height=config.vision.max_image_height,
            max_keypoints=config.vision.max_keypoints_per_image,
        ),
    )
    results = retriever.search(
        Query(
            modality=Modality.IMAGE,
            image_path=image_path,
            product_id=args.product_id,
        ),
        top_k=args.top_k,
    )
    print(json.dumps([result.model_dump(mode="json") for result in results], indent=2))


if __name__ == "__main__":
    main()





