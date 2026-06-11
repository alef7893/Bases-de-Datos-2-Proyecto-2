"""Similarity retrieval, ranking, catalog, and multimodal fusion."""

from .catalog import ProductCatalog
from .fusion import WeightedScoreFusion
from .text_retriever import TextRetriever
from .visual_retriever import VisualRetriever

__all__ = [
    "ProductCatalog",
    "TextRetriever",
    "VisualRetriever",
    "WeightedScoreFusion",
]
