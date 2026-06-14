"""Backend composition root for application services."""

from __future__ import annotations

from dataclasses import dataclass

from src.common.config import ProjectConfig
from src.common.models import Modality
from src.retrieval.custom.text.retriever import TextRetriever
from src.retrieval.custom.image.retriever import VisualRetriever
from src.retrieval.shared.catalog import ProductCatalog
from src.retrieval.shared.fusion import WeightedScoreFusion
from src.pipeline.text.codebook import TextCodebook
from src.pipeline.text.extractor import TextFeatureExtractor
from src.pipeline.image.codebook import VisualCodebook
from src.pipeline.image.sift_extractor import SIFTExtractor
from src.pipeline.image.encoder import VisualHistogramEncoder
from src.retrieval.postgres.image import PgvectorHNSWRetriever, PgvectorVisualRepository
from src.retrieval.postgres.text import PostgresGINTextRetriever, PostgresTextRepository

from .app04_multimodal_recommender import MultimodalRecommender
from .app01_visual_search import VisualSearch


@dataclass(frozen=True)
class ApplicationBackend:
    catalog: ProductCatalog
    visual_search: VisualSearch
    multimodal_recommender: MultimodalRecommender
    visual_search_hnsw: VisualSearch | None = None
    multimodal_recommender_postgres: MultimodalRecommender | None = None


def build_application_backend(config: ProjectConfig, scale: str | None = None) -> ApplicationBackend:
    active_scale = scale or config.data.active_scale
    artifacts = config.paths.artifacts_dir
    catalog = ProductCatalog.from_artifacts(
        artifacts / "catalog" / "products.jsonl",
        artifacts / "partitions" / f"{active_scale}.json",
    )
    text_dir = artifacts / "text" / active_scale
    vision_dir = artifacts / "vision" / active_scale
    text_extractor = TextFeatureExtractor(
        lowercase=config.text.lowercase,
        remove_stopwords=config.text.remove_stopwords,
        stemmer=config.text.stemmer,
    )
    text_retriever = TextRetriever(
        text_dir / "index",
        TextCodebook.load(text_dir / "codebook.json"),
        text_extractor,
    )
    visual_retriever = VisualRetriever(
        vision_dir / "index",
        VisualCodebook.load(vision_dir / "codebook.joblib"),
        SIFTExtractor(
            max_width=config.vision.max_image_width,
            max_height=config.vision.max_image_height,
            max_keypoints=config.vision.max_keypoints_per_image,
        ),
    )
    fusion = WeightedScoreFusion(
        {
            Modality.TEXT: config.applications.multimodal_weights["text"],
            Modality.IMAGE: config.applications.multimodal_weights["image"],
        }
    )
    return ApplicationBackend(
        catalog=catalog,
        visual_search=VisualSearch(catalog, visual_retriever),
        multimodal_recommender=MultimodalRecommender(
            catalog,
            text_retriever,
            visual_retriever,
            fusion,
            candidate_multiplier=config.applications.candidate_multiplier,
        ),
    )


def build_application_backend_with_hnsw(config: ProjectConfig, scale: str | None = None) -> ApplicationBackend:
    backend = build_application_backend(config, scale=scale)
    active_scale = scale or config.data.active_scale
    vision_dir = config.paths.artifacts_dir / "vision" / active_scale
    codebook = VisualCodebook.load(vision_dir / "codebook.joblib")
    extractor = SIFTExtractor(
        max_width=config.vision.max_image_width,
        max_height=config.vision.max_image_height,
        max_keypoints=config.vision.max_keypoints_per_image,
    )
    retriever = PgvectorHNSWRetriever(
        PgvectorVisualRepository(config.postgres),
        VisualHistogramEncoder(codebook, extractor),
        scale=active_scale,
        ef_search=config.phase3.hnsw_ef_search,
    )
    return ApplicationBackend(
        catalog=backend.catalog,
        visual_search=backend.visual_search,
        multimodal_recommender=backend.multimodal_recommender,
        visual_search_hnsw=VisualSearch(backend.catalog, retriever),
    )


def build_application_backend_with_postgres(
    config: ProjectConfig,
    scale: str | None = None,
) -> ApplicationBackend:
    backend = build_application_backend_with_hnsw(config, scale=scale)
    active_scale = scale or config.data.active_scale
    text_retriever = PostgresGINTextRetriever(
        PostgresTextRepository(config.postgres),
        scale=active_scale,
    )
    visual_retriever = backend.visual_search_hnsw.retriever
    fusion = WeightedScoreFusion(
        {
            Modality.TEXT: config.applications.multimodal_weights["text"],
            Modality.IMAGE: config.applications.multimodal_weights["image"],
        }
    )
    return ApplicationBackend(
        catalog=backend.catalog,
        visual_search=backend.visual_search,
        multimodal_recommender=backend.multimodal_recommender,
        visual_search_hnsw=backend.visual_search_hnsw,
        multimodal_recommender_postgres=MultimodalRecommender(
            backend.catalog,
            text_retriever,
            visual_retriever,
            fusion,
            candidate_multiplier=config.applications.candidate_multiplier,
        ),
    )

