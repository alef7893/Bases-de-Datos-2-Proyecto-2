"""Acoustic-word histogram construction."""

from __future__ import annotations

import numpy as np


def build_audio_histogram(assignments: np.ndarray, codebook_size: int) -> np.ndarray:
    """
    Build a normalized histogram from acoustic word assignments.
    """
    if codebook_size <= 0:
        raise ValueError("codebook_size must be positive")

    histogram = np.bincount(assignments, minlength=codebook_size).astype(np.float32)

    norm = np.linalg.norm(histogram)

    if norm:
        histogram /= norm

    return histogram


def sparse_audio_histogram(histogram: np.ndarray) -> dict[int, float]:
    """
    Convert dense audio histogram into sparse dictionary format.
    """
    return {
        int(index): float(histogram[index])
        for index in np.flatnonzero(histogram)
    }