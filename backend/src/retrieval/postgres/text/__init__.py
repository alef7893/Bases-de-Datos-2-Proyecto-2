"""PostgreSQL native full-text retrieval using a GIN index."""

from .repository import PostgresTextRepository
from .retriever import PostgresGINTextRetriever

__all__ = ["PostgresGINTextRetriever", "PostgresTextRepository"]
