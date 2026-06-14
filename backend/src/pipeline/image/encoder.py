"""Shared image-to-histogram encoder used by visual retrieval engines."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from src.pipeline.image.sift_extractor import SIFTExtractor

from .codebook import VisualCodebook
from .histogram import build_visual_histogram


class VisualHistogramEncoder:
    def __init__(self, codebook: VisualCodebook, extractor: SIFTExtractor) -> None:
        self.codebook = codebook
        self.extractor = extractor

    def encode_path(self, image_path: str | Path) -> np.ndarray:
        descriptors = self.extractor.extract_path(image_path)
        assignments = self.codebook.transform(descriptors)
        return build_visual_histogram(assignments, self.codebook.size)


