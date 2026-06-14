"""Load and validate project configuration from YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Base configuration model that rejects unknown keys."""

    model_config = ConfigDict(extra="forbid")


class ProjectSettings(StrictModel):
    name: str = Field(min_length=1)
    seed: int = Field(ge=0)


class PathsConfig(StrictModel):
    dataset_root: Path
    artifacts_dir: Path
    reports_dir: Path


class DataConfig(StrictModel):
    active_scale: Literal["1k", "10k", "full"]
    partition_sizes: dict[Literal["1k", "10k", "full"], int | None]
    split_ratios: dict[Literal["train", "validation", "test"], float]

    @field_validator("partition_sizes")
    @classmethod
    def validate_partition_sizes(
        cls, sizes: dict[str, int | None]
    ) -> dict[str, int | None]:
        for name, size in sizes.items():
            if name != "full" and (size is None or size <= 0):
                raise ValueError(f"partition size must be positive: {name}")
        return sizes

    @field_validator("split_ratios")
    @classmethod
    def validate_split_ratios(cls, ratios: dict[str, float]) -> dict[str, float]:
        if any(value <= 0 for value in ratios.values()):
            raise ValueError("all split ratios must be positive")
        if abs(sum(ratios.values()) - 1.0) > 1e-9:
            raise ValueError("split ratios must sum to 1.0")
        return ratios


class LoggingConfig(StrictModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


class TextConfig(StrictModel):
    language: str = "english"
    lowercase: bool = True
    remove_stopwords: bool = True
    stemmer: Literal["porter", "snowball", "none"] = "porter"
    codebook_size: int = Field(gt=0)
    min_document_frequency: int = Field(gt=0)
    chunk_max_tokens: int = Field(gt=0)
    chunk_overlap_tokens: int = Field(ge=0)
    spimi_max_postings_per_block: int = Field(gt=0)

    @field_validator("chunk_overlap_tokens")
    @classmethod
    def validate_chunk_overlap(cls, overlap: int, info: Any) -> int:
        max_tokens = info.data.get("chunk_max_tokens")
        if max_tokens is not None and overlap >= max_tokens:
            raise ValueError("chunk_overlap_tokens must be smaller than chunk_max_tokens")
        return overlap


class VisionConfig(StrictModel):
    max_image_width: int = Field(gt=0)
    max_image_height: int = Field(gt=0)
    max_keypoints_per_image: int = Field(gt=0)
    descriptor_sample_size: int = Field(gt=0)
    codebook_size: int = Field(gt=0)
    random_state: int = Field(ge=0)


class PostgresConfig(StrictModel):
    host: str = Field(min_length=1)
    port: int = Field(gt=0, le=65535)
    database: str = Field(min_length=1)
    user: str = Field(min_length=1)
    password_env: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)


class ApplicationsConfig(StrictModel):
    candidate_multiplier: int = Field(gt=0)
    multimodal_weights: dict[Literal["text", "image"], float]

    @field_validator("multimodal_weights")
    @classmethod
    def validate_multimodal_weights(cls, weights: dict[str, float]) -> dict[str, float]:
        if any(value < 0 for value in weights.values()):
            raise ValueError("multimodal weights cannot be negative")
        if abs(sum(weights.values()) - 1.0) > 1e-9:
            raise ValueError("multimodal weights must sum to 1.0")
        return weights


class Phase3Config(StrictModel):
    hnsw_m: int = Field(gt=0)
    hnsw_ef_construction: int = Field(gt=0)
    hnsw_ef_search: int = Field(gt=0)
    comparison_query_count: int = Field(gt=0)


class ProjectConfig(StrictModel):
    project: ProjectSettings
    paths: PathsConfig
    data: DataConfig
    logging: LoggingConfig
    text: TextConfig
    vision: VisionConfig
    postgres: PostgresConfig
    applications: ApplicationsConfig
    phase3: Phase3Config

    @field_validator("paths")
    @classmethod
    def validate_distinct_output_paths(cls, paths: PathsConfig) -> PathsConfig:
        if paths.artifacts_dir == paths.reports_dir:
            raise ValueError("artifacts_dir and reports_dir must be different")
        return paths


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as stream:
        content = yaml.safe_load(stream) or {}
    if not isinstance(content, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")
    return content


def _resolve_paths(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    resolved = _deep_merge({}, config)
    paths = resolved.get("paths", {})
    for key in ("dataset_root", "artifacts_dir", "reports_dir"):
        value = Path(paths[key])
        paths[key] = value if value.is_absolute() else (project_root / value).resolve()
    return resolved


def load_project_config(
    config_dir: str | Path = "configs",
    project_root: str | Path | None = None,
) -> ProjectConfig:
    """Load all project YAML files and return a validated configuration."""

    root = Path(project_root or Path.cwd()).resolve()
    directory = Path(config_dir)
    if not directory.is_absolute():
        directory = root / directory

    merged: dict[str, Any] = {}
    for filename in (
        "base.yaml",
        "text.yaml",
        "vision.yaml",
        "postgres.yaml",
        "applications.yaml",
        "phase3.yaml",
    ):
        merged = _deep_merge(merged, _read_yaml(directory / filename))

    return ProjectConfig.model_validate(_resolve_paths(merged, root))
