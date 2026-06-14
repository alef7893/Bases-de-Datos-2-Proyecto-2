"""Build the canonical product catalog and reproducible partition manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.common.config import load_project_config
from src.common.logging import configure_logging
from src.pipeline.catalog.loader import FashionDatasetLoader, read_catalog
from src.pipeline.catalog.partitions import build_partition_manifests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional product limit for a quick validation run.",
    )
    parser.add_argument(
        "--skip-duplicate-hashes",
        action="store_true",
        help="Skip byte-identical image grouping. Intended only for quick checks.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_project_config()
    configure_logging(config.logging)

    loader = FashionDatasetLoader(config.paths.dataset_root)
    duplicate_groups = (
        {} if args.skip_duplicate_hashes else loader.find_duplicate_image_groups()
    )
    catalog_path = config.paths.artifacts_dir / "catalog" / "products.jsonl"
    count = loader.write_catalog(
        catalog_path,
        duplicate_groups=duplicate_groups,
        limit=args.limit,
    )
    manifests = build_partition_manifests(
        read_catalog(catalog_path),
        partition_sizes=config.data.partition_sizes,
        split_ratios=config.data.split_ratios,
        output_dir=config.paths.artifacts_dir / "partitions",
        seed=config.project.seed,
    )
    summary = {
        "catalog": str(catalog_path),
        "products": count,
        "duplicate_products": len(duplicate_groups),
        "manifests": {name: str(path) for name, path in manifests.items()},
    }
    summary_path = config.paths.artifacts_dir / "catalog" / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()





