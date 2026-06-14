"""Image loading and deterministic aspect-ratio-preserving resizing."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_grayscale_image(
    path: str | Path, max_width: int, max_height: int
) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")

    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height, 1.0)
    if scale < 1.0:
        image = cv2.resize(
            image,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return image
