"""Protocolos comunes que deben implementar los componentes del pipeline y recuperación."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence, runtime_checkable

from .models import Chunk, Product, Query, SearchResult

# Contrato para dividir un producto en chunks específicos de una modalidad.
@runtime_checkable
class Splitter(Protocol):
    def split(self, product: Product) -> Sequence[Chunk]:
        """Divide un producto en chunks específicos de una modalidad."""

# Contrato para extraer características desde un chunk previamente generado.
@runtime_checkable
class FeatureExtractor(Protocol):
    def extract(self, chunk: Chunk) -> Any:
        """Extrae características específicas de la modalidad desde un chunk."""

# Contrato para entrenar, aplicar y persistir un vocabulario finito de codewords.
@runtime_checkable
class Codebook(Protocol):
    def fit(self, features: Iterable[Any]) -> None:
        """Entrena un codebook usando características de entrenamiento."""

    def transform(self, features: Any) -> Any:
        """Cuantiza o asigna características a codewords."""

    def save(self, path: Path) -> None:
        """Persiste el codebook en la ruta indicada."""

# Contrato para construir y persistir un índice a partir de elementos preparados.
@runtime_checkable
class Indexer(Protocol):
    def build(self, items: Iterable[Any]) -> None:
        """Construye el índice a partir de elementos preparados."""

    def save(self, path: Path) -> None:
        """Persiste el índice en la ruta indicada."""

# Contrato común para ejecutar consultas y devolver productos ordenados por relevancia.
@runtime_checkable
class Retriever(Protocol):
    def search(self, query: Query, top_k: int = 10) -> Sequence[SearchResult]:
        """Devuelve los productos mejor posicionados para una consulta."""
