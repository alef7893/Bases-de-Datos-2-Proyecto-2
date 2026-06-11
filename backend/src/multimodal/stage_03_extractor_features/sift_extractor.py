"""SIFT descriptor extraction with per-product checkpoint files."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .image_preprocessing import load_grayscale_image


class SIFTExtractor:
    def __init__(
        self,
        max_width: int,
        max_height: int,
        max_keypoints: int,
    ) -> None:
        if min(max_width, max_height, max_keypoints) <= 0:
            raise ValueError("SIFT extraction parameters must be positive")
        self.max_width = max_width
        self.max_height = max_height
        self.max_keypoints = max_keypoints
        self.sift = cv2.SIFT_create(nfeatures=max_keypoints)

    def extract_path(self, path: str | Path) -> np.ndarray:
        image = load_grayscale_image(path, self.max_width, self.max_height)
        _, descriptors = self.sift.detectAndCompute(image, None)
        if descriptors is None:
            return np.empty((0, 128), dtype=np.float32)
        return descriptors.astype(np.float32, copy=False)

    def extract_with_checkpoint(
        self,
        product_id: int,
        image_path: str | Path,
        checkpoint_dir: str | Path,
    ) -> np.ndarray:
        output = Path(checkpoint_dir)
        output.mkdir(parents=True, exist_ok=True)
        checkpoint = output / f"{product_id}.npy"
        if checkpoint.is_file():
            return np.load(checkpoint, allow_pickle=False)
        descriptors = self.extract_path(image_path)
        np.save(checkpoint, descriptors, allow_pickle=False)
        return descriptors

