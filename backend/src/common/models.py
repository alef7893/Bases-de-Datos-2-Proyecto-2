"""Modelos de dominio validados y compartidos por todos los motores de recuperación."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Modelo base estricto que rechaza campos desconocidos para detectar datos o configuraciones inválidas.
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

# Enumera las modalidades que pueden procesar las consultas, chunks y resultados del sistema.
class Modality(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"
    AUDIO = "audio"

# Representa un producto canónico que enlaza texto, imagen, categorías y metadatos de la dataset.
class Product(StrictModel):
    product_id: int = Field(gt=0)
    canonical_text: str = ""
    image_path: Path | None = None
    categories: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    has_image: bool = False
    has_description: bool = False
    duplicate_image_group: str | None = None

    @field_validator("canonical_text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.split())

# Representa una unidad atómica de contenido asociada a un producto y a una modalidad.
class Chunk(StrictModel):
    chunk_id: str = Field(min_length=1)
    product_id: int = Field(gt=0)
    modality: Modality
    position: int = Field(ge=0)
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

# Describe una consulta que puede contener texto, imagen, producto de referencia y metadatos adicionales.
class Query(StrictModel):
    modality: Modality
    text: str | None = None
    image_path: Path | None = None
    product_id: int | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def normalize_query_text(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value else value

# Representa un producto recuperado, incluyendo su puntuación, posición y modalidad de búsqueda.
class SearchResult(StrictModel):
    product_id: int = Field(gt=0)
    score: float
    rank: int = Field(gt=0)
    modality: Modality
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("score")
    @classmethod
    def score_must_be_finite(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("score must be finite")
        return value

# Registra la identidad, ubicación y parámetros necesarios para reproducir un codebook.
class CodebookMetadata(StrictModel):
    modality: Modality
    version: str = Field(min_length=1)
    size: int = Field(gt=0)
    artifact_path: Path
    parameters: dict[str, Any] = Field(default_factory=dict)

# Registra la configuración básica y el momento de inicio de una ejecución experimental.
class ExperimentRun(StrictModel):
    run_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    seed: int = Field(ge=0)
    scale: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
