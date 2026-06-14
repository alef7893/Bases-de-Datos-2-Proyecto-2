from pathlib import Path

import numpy as np

from src.common.models import Modality, Query, SearchResult
from src.experiments.common.metrics import latency_summary, precision_at_k, recall_at_k
from src.experiments.common.plots import generate_phase4_plots
from src.retrieval.postgres.image.retriever import PgvectorHNSWRetriever


class FakeEncoder:
    def encode_path(self, image_path):
        return np.array([0.0, 1.0], dtype=np.float32)


class FakeRepository:
    def __init__(self):
        self.calls = []

    def search(self, histogram, **parameters):
        self.calls.append((histogram, parameters))
        return [(2, 0.9), (3, 0.7)]


def test_hnsw_retriever_uses_shared_histogram_and_excludes_query_product() -> None:
    repository = FakeRepository()
    retriever = PgvectorHNSWRetriever(repository, FakeEncoder(), scale="1k")

    results = retriever.search(
        Query(modality=Modality.IMAGE, image_path=Path("query.jpg"), product_id=1),
        top_k=2,
    )

    assert [result.product_id for result in results] == [2, 3]
    assert repository.calls[0][1]["exclude_product_id"] == 1
    assert repository.calls[0][1]["scale"] == "1k"


def test_recall_at_k_uses_exact_results_as_reference() -> None:
    reference = [
        SearchResult(product_id=1, score=1, rank=1, modality=Modality.IMAGE),
        SearchResult(product_id=2, score=0.9, rank=2, modality=Modality.IMAGE),
    ]
    results = [
        SearchResult(product_id=2, score=1, rank=1, modality=Modality.IMAGE),
        SearchResult(product_id=3, score=0.8, rank=2, modality=Modality.IMAGE),
    ]

    assert recall_at_k(results, reference, 2) == 0.5


def test_phase4_quality_and_latency_metrics() -> None:
    results = [
        SearchResult(product_id=2, score=1, rank=1, modality=Modality.IMAGE),
        SearchResult(product_id=3, score=0.8, rank=2, modality=Modality.IMAGE),
    ]

    assert precision_at_k(results, {2}, 2) == 0.5
    assert latency_summary([10, 20, 30]) == {
        "mean_ms": 20,
        "median_ms": 20,
        "p95_ms": 30,
        "min_ms": 10,
        "max_ms": 30,
    }


def test_phase4_generates_svg_plots(tmp_path: Path) -> None:
    report = {
        "latency": {name: {"mean_ms": value} for name, value in {"custom": 1, "hnsw": 2, "exact": 3}.items()},
        "throughput_queries_per_second": {"custom": 3, "hnsw": 2, "exact": 1},
        "quality": {"precision_at_k": {"custom": 0.5, "hnsw": 0.6, "exact": 0.7}},
        "memory_and_storage": {
            "custom_index_disk_bytes": 1024,
            "hnsw_index_disk_bytes": 2048,
        },
    }

    paths = generate_phase4_plots(report, tmp_path)

    assert len(paths) == 4
    assert all(path.read_text(encoding="utf-8").startswith("<svg") for path in paths)
