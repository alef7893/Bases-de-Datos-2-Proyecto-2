"""Image implementation of the unified multimodal pipeline."""

from .codebook import VisualCodebook
from .encoder import VisualHistogramEncoder
from .sift_extractor import SIFTExtractor

__all__ = [
    "SIFTExtractor",
    "VisualCodebook",
    "VisualHistogramEncoder",
]
