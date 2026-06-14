"""Compare the custom and PostgreSQL retrieval engines used by application 04."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from src.applications.backend import build_application_backend_with_postgres
from src.common.config import load_project_config
from src.experiments.common.metrics import latency_summary, precision_at_k, recall_at_k


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
    backend = build_application_backend_with_postgres(config, scale=scale)
    postgres = backend.multimodal_recommender_postgres
    if postgres is None:
        raise RuntimeError("PostgreSQL multimodal recommender is not configured")

    manifest = json.loads(
        (config.paths.artifacts_dir / "partitions" / f"{scale}.json").read_text(
            encoding="utf-8"
        )
    )
    test_ids = set(manifest["splits"]["test"])
    products = [
        product
        for product in backend.catalog.products()
        if product.has_image and product.canonical_text and product.product_id in test_ids
    ][:query_count]
    if not products:
        raise ValueError("No multimodal test products are available for the selected scale")

    records = []
    for product in products:
        category = product.categories.get("articleType")
        relevant_ids = {
            candidate.product_id
            for candidate in backend.catalog.products()
            if category
            and candidate.product_id != product.product_id
            and candidate.categories.get("articleType") == category
        }
        custom_results, custom_ms = _timed(
            lambda: backend.multimodal_recommender.recommend(
                product.product_id, top_k=args.top_k
            )
        )
        postgres_results, postgres_ms = _timed(
            lambda: postgres.recommend(product.product_id, top_k=args.top_k)
        )
        records.append(
            {
                "product_id": product.product_id,
                "article_type": category,
                "custom_ms": custom_ms,
                "postgres_ms": postgres_ms,
                "custom_precision_at_k": precision_at_k(
                    custom_results, relevant_ids, args.top_k
                ),
                "postgres_precision_at_k": precision_at_k(
                    postgres_results, relevant_ids, args.top_k
                ),
                "ranking_overlap_at_k": recall_at_k(
                    postgres_results, custom_results, args.top_k
                ),
            }
        )

    custom_times = [record["custom_ms"] for record in records]
    postgres_times = [record["postgres_ms"] for record in records]
    custom_index_paths = (
        config.paths.artifacts_dir / "text" / scale / "index" / "postings.jsonl",
        config.paths.artifacts_dir / "vision" / scale / "index" / "postings.jsonl",
    )
    text_repository = postgres.text_retriever.repository
    visual_repository = postgres.visual_retriever.repository
    report = {
        "scale": scale,
        "top_k": args.top_k,
        "queries": len(records),
        "latency": {
            "custom": latency_summary(custom_times),
            "postgres_gin_hnsw": latency_summary(postgres_times),
        },
        "throughput_queries_per_second": {
            "custom": 1000 / mean(custom_times),
            "postgres_gin_hnsw": 1000 / mean(postgres_times),
        },
        "quality": {
            "custom_precision_at_k": mean(
                record["custom_precision_at_k"] for record in records
            ),
            "postgres_precision_at_k": mean(
                record["postgres_precision_at_k"] for record in records
            ),
            "ranking_overlap_at_k": mean(
                record["ranking_overlap_at_k"] for record in records
            ),
        },
        "index_storage_bytes": {
            "custom_text_and_image": sum(Path(path).stat().st_size for path in custom_index_paths),
            "postgres_gin": text_repository.index_size_bytes(),
            "pgvector_hnsw": visual_repository.index_size_bytes(scale),
        },
        "records": records,
    }
    output = (
        config.paths.reports_dir
        / "phase3"
        / f"multimodal_app04_comparison_{scale}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("latency", "quality")}, indent=2))
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
