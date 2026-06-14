from pathlib import Path

from src.common.models import Modality, Query
from src.experiments.common.plots import generate_multimodal_phase4_plots
from src.retrieval.postgres.text.retriever import PostgresGINTextRetriever


class FakeTextRepository:
    def __init__(self):
        self.calls = []

    def search(self, text, **parameters):
        self.calls.append((text, parameters))
        return [(2, 0.8), (3, 0.4)]


def test_postgres_gin_retriever_accepts_multimodal_queries() -> None:
    repository = FakeTextRepository()
    retriever = PostgresGINTextRetriever(repository, scale="1k")

    results = retriever.search(
        Query(
            modality=Modality.MULTIMODAL,
            text="black sports shoes",
            image_path=Path("query.jpg"),
            product_id=1,
        ),
        top_k=2,
    )

    assert [result.product_id for result in results] == [2, 3]
    assert results[0].metadata["engine"] == "postgres_gin"
    assert repository.calls[0][1] == {
        "scale": "1k",
        "top_k": 2,
        "exclude_product_id": 1,
    }


def test_postgres_gin_retriever_returns_no_results_for_empty_text() -> None:
    repository = FakeTextRepository()
    retriever = PostgresGINTextRetriever(repository, scale="1k")

    assert retriever.search(Query(modality=Modality.TEXT, text="")) == []
    assert repository.calls == []


def test_phase3_sql_defines_native_gin_index() -> None:
    sql = (
        Path(__file__).parents[2] / "sql" / "004_phase3_text_gin.sql"
    ).read_text(encoding="utf-8")

    assert "search_vector tsvector" in sql
    assert "USING gin (search_vector)" in sql


def test_phase4_multimodal_generates_svg_plots(tmp_path: Path) -> None:
    report = {
        "latency": {
            "custom": {"mean_ms": 1},
            "postgres_gin_hnsw": {"mean_ms": 2},
        },
        "throughput_queries_per_second": {
            "custom": 3,
            "postgres_gin_hnsw": 2,
        },
        "quality": {
            "precision_at_k": {"custom": 0.5, "postgres_gin_hnsw": 0.6}
        },
        "memory_and_storage": {
            "custom_index_disk_bytes": 1024,
            "postgres_index_disk_bytes": 2048,
        },
    }

    paths = generate_multimodal_phase4_plots(report, tmp_path)

    assert len(paths) == 4
    assert all(path.read_text(encoding="utf-8").startswith("<svg") for path in paths)
