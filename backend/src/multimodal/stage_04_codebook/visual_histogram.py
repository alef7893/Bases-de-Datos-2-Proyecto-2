"""Visual-word histogram construction."""

from __future__ import annotations

import numpy as np


def build_visual_histogram(assignments: np.ndarray, codebook_size: int) -> np.ndarray:
    histogram = np.bincount(assignments, minlength=codebook_size).astype(np.float32)
    norm = np.linalg.norm(histogram)
    if norm:
        histogram /= norm
    return histogram


def sparse_visual_histogram(histogram: np.ndarray) -> dict[int, float]:
    return {
        int(index): float(histogram[index])
        for index in np.flatnonzero(histogram)
    }
