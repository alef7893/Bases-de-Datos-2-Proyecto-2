"""Feature extractors and modality-specific preprocessing."""

from .image_preprocessing import load_grayscale_image
from .sift_extractor import SIFTExtractor
from .text_extractor import TextFeatureExtractor

__all__ = ["SIFTExtractor", "TextFeatureExtractor", "load_grayscale_image"]
