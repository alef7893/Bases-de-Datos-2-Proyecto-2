"""Backend composition root for application services."""

from __future__ import annotations

from dataclasses import dataclass

from src.common.config import ProjectConfig
from src.common.models import Modality
from src.multimodal.stage_06_similarity_search.text_retriever import TextRetriever
from src.multimodal.stage_06_similarity_search.visual_retriever import VisualRetriever
from src.multimodal.stage_06_similarity_search.catalog import ProductCatalog
from src.multimodal.stage_06_similarity_search.fusion import WeightedScoreFusion
from src.multimodal.stage_04_codebook.text_codebook import TextCodebook
from src.multimodal.stage_03_extractor_features.text_extractor import TextFeatureExtractor
from src.multimodal.stage_04_codebook.visual_codebook import VisualCodebook
from src.multimodal.stage_03_extractor_features.sift_extractor import SIFTExtractor

from .multimodal_recommender import MultimodalRecommender
from .visual_search import VisualSearch


@dataclass(frozen=True)
class ApplicationBackend:
    catalog: ProductCatalog
    visual_search: VisualSearch
    multimodal_recommender: MultimodalRecommender


def build_phase2_backend(config: ProjectConfig, scale: str | None = None) -> ApplicationBackend:
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



