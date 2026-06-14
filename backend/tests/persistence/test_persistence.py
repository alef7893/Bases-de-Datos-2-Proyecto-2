from pathlib import Path

from src.persistence.postgres_client import PostgresClient
from src.persistence.artifact_loader import ArtifactPostgresLoader


def test_sql_schema_contains_required_phase2_entities() -> None:
    schema = Path("sql/002_schema.sql").read_text(encoding="utf-8")

    for table in ArtifactPostgresLoader.TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema
    assert "visual_vector vector(512)" in schema


def test_phase3_schema_creates_visual_hnsw_index() -> None:
    schema = Path("sql/003_phase3_hnsw.sql").read_text(encoding="utf-8")

    assert "USING hnsw" in schema
    assert "visual_vector vector_cosine_ops" in schema


def test_postgres_client_exposes_phase2_operations() -> None:
    assert callable(PostgresClient.connect)
    assert callable(PostgresClient.apply_sql_directory)
    assert callable(PostgresClient.fetch_counts)
