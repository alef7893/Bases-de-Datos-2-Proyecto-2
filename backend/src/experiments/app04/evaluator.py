"""Complete experimental evaluator for application 04 retrieval engines."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean
from time import perf_counter

from src.applications.backend import build_application_backend_with_postgres
from src.common.config import ProjectConfig
from src.common.models import Product
from src.experiments.common.metrics import latency_summary, precision_at_k, recall_at_k

from src.experiments.common.instrumentation import (
    deep_size,
    peak_python_bytes,
    summarize_plan_io,
    timed,
)


class MultimodalPhase4Evaluator:
    ENGINES = ("custom", "postgres_gin_hnsw")

    def __init__(self, config: ProjectConfig, scale: str) -> None:
        self.config = config
        self.scale = scale
        self.backend = build_application_backend_with_postgres(config, scale=scale)
        self.custom = self.backend.multimodal_recommender
        self.postgres = self.backend.multimodal_recommender_postgres
        if self.postgres is None:
            raise RuntimeError("PostgreSQL multimodal recommender is not configured")

    def evaluate(
        self,
        *,
        query_count: int,
        top_k: int,
        repeats: int,
        concurrency: int,
    ) -> dict:
        if min(query_count, top_k, repeats, concurrency) <= 0:
            raise ValueError("experimental parameters must be positive")
        products = self._test_products(query_count)
        latencies = {engine: [] for engine in self.ENGINES}
        precisions = {engine: [] for engine in self.ENGINES}
        overlaps: list[float] = []
        records: list[dict] = []

        for repeat in range(repeats):
            for product in products:
                results = {}
                for engine in self.ENGINES:
                    engine_results, elapsed = timed(
                        lambda engine=engine: self._recommend(
                            engine, product.product_id, top_k
                        )
                    )
                    results[engine] = engine_results
                    latencies[engine].append(elapsed)
                    precisions[engine].append(
                        precision_at_k(
                            engine_results,
                            self._relevant_ids(product),
                            top_k,
                        )
                    )
                overlaps.append(
                    recall_at_k(
                        results["postgres_gin_hnsw"],
                        results["custom"],
                        top_k,
                    )
                )
                records.append(
                    {
                        "repeat": repeat + 1,
                        "product_id": product.product_id,
                        "article_type": product.categories.get("articleType", ""),
                        **{
                            f"{engine}_latency_ms": latencies[engine][-1]
                            for engine in self.ENGINES
                        },
                        **{
                            f"{engine}_precision_at_k": precisions[engine][-1]
                            for engine in self.ENGINES
                        },
                        "ranking_overlap_at_k": overlaps[-1],
                    }
                )

        throughput = {
            engine: self._concurrent_throughput(engine, products, top_k, concurrency)
            for engine in self.ENGINES
        }
        sample = products[0]
        visual_histogram = self.postgres.visual_retriever.encoder.encode_path(
            sample.image_path
        )
        text_plan = self.postgres.text_retriever.repository.explain_search(
            sample.canonical_text,
            scale=self.scale,
            top_k=top_k,
        )
        visual_plan = self.postgres.visual_retriever.repository.explain_search(
            visual_histogram,
            scale=self.scale,
            top_k=top_k,
            method="hnsw",
        )
        text_postings = self.custom.text_retriever.postings
        visual_postings = self.custom.visual_retriever.postings
        custom_paths = self._custom_index_paths()
        gin_bytes = self.postgres.text_retriever.repository.index_size_bytes()
        hnsw_bytes = self.postgres.visual_retriever.repository.index_size_bytes(
            self.scale
        )
        return {
            "application": "app04_multimodal_recommender",
            "scale": self.scale,
            "products": len(self.backend.catalog),
            "queries": len(products),
            "repeats": repeats,
            "top_k": top_k,
            "concurrency": concurrency,
            "relevance_definition": "same articleType as the query product",
            "latency": {
                engine: latency_summary(values)
                for engine, values in latencies.items()
            },
            "throughput_queries_per_second": throughput,
            "quality": {
                "precision_at_k": {
                    engine: mean(values) for engine, values in precisions.items()
                },
                "ranking_overlap_at_k": mean(overlaps),
            },
            "memory_and_storage": {
                "custom_text_index_memory_bytes": deep_size(text_postings),
                "custom_visual_index_memory_bytes": deep_size(visual_postings),
                "custom_index_memory_bytes": deep_size(text_postings)
                + deep_size(visual_postings),
                "custom_text_index_disk_bytes": custom_paths[0].stat().st_size,
                "custom_visual_index_disk_bytes": custom_paths[1].stat().st_size,
                "custom_index_disk_bytes": sum(path.stat().st_size for path in custom_paths),
                "gin_index_disk_bytes": gin_bytes,
                "hnsw_index_disk_bytes": hnsw_bytes,
                "postgres_index_disk_bytes": gin_bytes + hnsw_bytes,
                "custom_query_peak_python_bytes": peak_python_bytes(
                    lambda: self._recommend("custom", sample.product_id, top_k)
                ),
                "postgres_query_peak_python_bytes": peak_python_bytes(
                    lambda: self._recommend(
                        "postgres_gin_hnsw", sample.product_id, top_k
                    )
                ),
            },
            "postgres_io": {
                "gin_text": summarize_plan_io(text_plan),
                "hnsw_image": summarize_plan_io(visual_plan),
                "plans": {"gin_text": text_plan, "hnsw_image": visual_plan},
            },
            "records": records,
        }

    def _recommend(self, engine: str, product_id: int, top_k: int):
        recommender = self.custom if engine == "custom" else self.postgres
        return recommender.recommend(product_id, top_k=top_k)

    def _test_products(self, query_count: int) -> list[Product]:
        manifest = json.loads(
            (
                self.config.paths.artifacts_dir
                / "partitions"
                / f"{self.scale}.json"
            ).read_text(encoding="utf-8")
        )
        test_ids = set(manifest["splits"]["test"])
        products = [
            product
            for product in self.backend.catalog.products()
            if product.has_image
            and product.canonical_text
            and product.product_id in test_ids
        ][:query_count]
        if not products:
            raise ValueError(
                f"No multimodal test products available for scale {self.scale}"
            )
        return products

    def _relevant_ids(self, query: Product) -> set[int]:
        article_type = query.categories.get("articleType")
        if not article_type:
            return set()
        return {
            product.product_id
            for product in self.backend.catalog.products()
            if product.product_id != query.product_id
            and product.categories.get("articleType") == article_type
        }

    def _concurrent_throughput(
        self,
        engine: str,
        products: list[Product],
        top_k: int,
        concurrency: int,
    ) -> float:
        started = perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(self._recommend, engine, product.product_id, top_k)
                for product in products
            ]
            for future in futures:
                future.result()
        elapsed = perf_counter() - started
        return len(products) / elapsed

    def _custom_index_paths(self) -> tuple[Path, Path]:
        artifacts = self.config.paths.artifacts_dir
        return (
            artifacts / "text" / self.scale / "index" / "postings.jsonl",
            artifacts / "vision" / self.scale / "index" / "postings.jsonl",
        )
