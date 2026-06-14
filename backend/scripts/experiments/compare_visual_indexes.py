"""Compare the custom visual index against pgvector exact search and HNSW."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from src.applications.backend import build_application_backend_with_hnsw
from src.common.config import load_project_config
from src.experiments.common.metrics import recall_at_k


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--queries", type=int, default=None)
    return parser.parse_args()


def _timed(call):
    started = perf_counter()
    result = call()
    return result, (perf_counter() - started) * 1000


def main() -> None:
    args = parse_args()
    if args.top_k <= 0 or (args.queries is not None and args.queries <= 0):
        raise ValueError("top-k and queries must be positive")

    config = load_project_config()
    scale = args.scale or config.data.active_scale
    query_count = args.queries or config.phase3.comparison_query_count
    backend = build_application_backend_with_hnsw(config, scale=scale)
    own = backend.visual_search.retriever
    hnsw = backend.visual_search_hnsw.retriever
    manifest = json.loads(
        (config.paths.artifacts_dir / "partitions" / f"{scale}.json").read_text(
            encoding="utf-8"
        )
    )
    test_ids = set(manifest["splits"]["test"])
    products = [
        product
        for product in backend.catalog.products()
        if product.has_image and product.product_id in test_ids
    ][:query_count]
    if not products:
        raise ValueError("No test images are available for the selected scale")

    records = []
    for product in products:
        histogram, encoding_ms = _timed(lambda: hnsw.encoder.encode_path(product.image_path))
        exact, exact_ms = _timed(
            lambda: hnsw.search_histogram(
                histogram,
                top_k=args.top_k,
                exclude_product_id=product.product_id,
                method="exact",
            )
        )
        hnsw_results, hnsw_ms = _timed(
            lambda: hnsw.search_histogram(
                histogram,
                top_k=args.top_k,
                exclude_product_id=product.product_id,
            )
        )
        own_results, own_ms = _timed(
            lambda: own.search_histogram(
                histogram,
                top_k=args.top_k,
                exclude_product_id=product.product_id,
            )
        )
        records.append(
            {
                "product_id": product.product_id,
                "encoding_ms": encoding_ms,
                "exact_ms": exact_ms,
                "hnsw_ms": hnsw_ms,
                "custom_ms": own_ms,
                "hnsw_recall_at_k": recall_at_k(hnsw_results, exact, args.top_k),
                "custom_recall_at_k": recall_at_k(own_results, exact, args.top_k),
            }
        )

    repository = hnsw.repository
    averages = {
        key: mean(record[key] for record in records)
        for key in (
            "encoding_ms",
            "exact_ms",
            "hnsw_ms",
            "custom_ms",
            "hnsw_recall_at_k",
            "custom_recall_at_k",
        )
    }
    custom_index_path = (
        config.paths.artifacts_dir / "vision" / scale / "index" / "postings.jsonl"
    )
    report = {
        "scale": scale,
        "top_k": args.top_k,
        "queries": len(records),
        "hnsw_index_size_bytes": repository.index_size_bytes(scale),
        "custom_index_size_bytes": Path(custom_index_path).stat().st_size,
        "throughput_queries_per_second": {
            "exact": 1000 / averages["exact_ms"],
            "hnsw": 1000 / averages["hnsw_ms"],
            "custom": 1000 / averages["custom_ms"],
        },
        "averages": averages,
        "records": records,
    }
    output = config.paths.reports_dir / "phase3" / f"visual_comparison_{scale}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["averages"], indent=2))
    print(f"Report: {output}")


if __name__ == "__main__":
    main()

