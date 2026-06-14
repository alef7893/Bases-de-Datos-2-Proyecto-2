"""Complete experimental evaluator for visual-search retrieval engines."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from statistics import mean
from time import perf_counter

from src.applications.backend import build_application_backend_with_hnsw
from src.common.config import ProjectConfig
from src.common.models import Product
from src.experiments.common.metrics import latency_summary, precision_at_k, recall_at_k
from src.experiments.common.instrumentation import (
    deep_size,
    peak_python_bytes,
    summarize_plan_io,
    timed,
)


class VisualPhase4Evaluator:
    ENGINES = ("custom", "hnsw", "exact")

    def __init__(self, config: ProjectConfig, scale: str) -> None:
        self.config = config
        self.scale = scale
        self.backend = build_application_backend_with_hnsw(config, scale=scale)
        self.custom = self.backend.visual_search.retriever
        self.hnsw = self.backend.visual_search_hnsw.retriever
        self.repository = self.hnsw.repository

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
        encoded = [
            (product, self.hnsw.encoder.encode_path(product.image_path))
            for product in products
        ]
        records: list[dict] = []
        latencies = {engine: [] for engine in self.ENGINES}
        precisions = {engine: [] for engine in self.ENGINES}
        recalls = {"custom": [], "hnsw": []}

        for repeat in range(repeats):
            for product, histogram in encoded:
                results = {}
                for engine in self.ENGINES:
                    engine_results, elapsed = timed(
                        lambda engine=engine: self._search(
                            engine, histogram, product.product_id, top_k
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
                recalls["custom"].append(recall_at_k(results["custom"], results["exact"], top_k))
                recalls["hnsw"].append(recall_at_k(results["hnsw"], results["exact"], top_k))
                records.append(
                    {
                        "repeat": repeat + 1,
                        "product_id": product.product_id,
                        "article_type": product.categories.get("articleType", ""),
                        **{f"{engine}_latency_ms": latencies[engine][-1] for engine in self.ENGINES},
                        **{f"{engine}_precision_at_k": precisions[engine][-1] for engine in self.ENGINES},
                        "custom_recall_at_k": recalls["custom"][-1],
                        "hnsw_recall_at_k": recalls["hnsw"][-1],
                    }
                )

        throughput = {
            engine: self._concurrent_throughput(engine, encoded, top_k, concurrency)
            for engine in self.ENGINES
        }
        sample_histogram = encoded[0][1]
        hnsw_plan = self.repository.explain_search(
            sample_histogram, scale=self.scale, top_k=top_k, method="hnsw"
        )
        exact_plan = self.repository.explain_search(
            sample_histogram, scale=self.scale, top_k=top_k, method="exact"
        )
        return {
            "application": "app01_visual_search",
            "scale": self.scale,
            "products": len(self.backend.catalog),
            "queries": len(products),
            "repeats": repeats,
            "top_k": top_k,
            "concurrency": concurrency,
            "latency": {engine: latency_summary(values) for engine, values in latencies.items()},
            "throughput_queries_per_second": throughput,
            "quality": {
                "precision_at_k": {engine: mean(values) for engine, values in precisions.items()},
                "recall_at_k_vs_exact": {engine: mean(values) for engine, values in recalls.items()},
            },
            "memory_and_storage": {
                "custom_index_memory_bytes": deep_size(self.custom.postings),
                "custom_index_disk_bytes": (
                    self.config.paths.artifacts_dir
                    / "vision"
                    / self.scale
                    / "index"
                    / "postings.jsonl"
                ).stat().st_size,
                "hnsw_index_disk_bytes": self.repository.index_size_bytes(self.scale),
                "custom_querypeak_python_bytes": peak_python_bytes(
                    lambda: self._search("custom", sample_histogram, None, top_k)
                ),
                "hnsw_querypeak_python_bytes": peak_python_bytes(
                    lambda: self._search("hnsw", sample_histogram, None, top_k)
                ),
            },
            "postgres_io": {
                "hnsw": summarize_plan_io(hnsw_plan),
                "exact": summarize_plan_io(exact_plan),
                "plans": {"hnsw": hnsw_plan, "exact": exact_plan},
            },
            "records": records,
        }

    def _search(self, engine: str, histogram, product_id: int | None, top_k: int):
        if engine == "custom":
            return self.custom.search_histogram(
                histogram, top_k=top_k, exclude_product_id=product_id
            )
        return self.hnsw.search_histogram(
            histogram,
            top_k=top_k,
            exclude_product_id=product_id,
            method=engine,
        )

    def _test_products(self, query_count: int) -> list[Product]:
        manifest = json.loads(
            (self.config.paths.artifacts_dir / "partitions" / f"{self.scale}.json").read_text(
                encoding="utf-8"
            )
        )
        test_ids = set(manifest["splits"]["test"])
        products = [
            product
            for product in self.backend.catalog.products()
            if product.has_image and product.product_id in test_ids
        ][:query_count]
        if not products:
            raise ValueError(f"No test images available for scale {self.scale}")
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

    def _concurrent_throughput(self, engine: str, encoded, top_k: int, concurrency: int) -> float:
        tasks = [
            (histogram, product.product_id)
            for product, histogram in encoded
        ]
        started = perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(self._search, engine, histogram, product_id, top_k)
                for histogram, product_id in tasks
            ]
            for future in futures:
                future.result()
        elapsed = perf_counter() - started
        return len(tasks) / elapsed

