"""Custom SPIMI text retrieval."""

from .inverted_index import SPIMIIndexer
from .retriever import TextRetriever

__all__ = ["SPIMIIndexer", "TextRetriever"]
