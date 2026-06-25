"""Shared audio-to-histogram encoder used by acoustic retrieval engines."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .codebook import AudioCodebook
from .histogram import build_audio_histogram
from .mfcc_extractor import MFCCExtractor


class AudioHistogramEncoder:
    def __init__(self, codebook: AudioCodebook, extractor: MFCCExtractor) -> None:
        self.codebook = codebook
        self.extractor = extractor

    def encode_path(self, audio_path: str | Path) -> np.ndarray:
        descriptors = self.extractor.extract_path(audio_path)
        assignments = self.codebook.transform(descriptors)
        return build_audio_histogram(assignments, self.codebook.size)