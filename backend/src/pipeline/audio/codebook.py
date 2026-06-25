"""K-Means acoustic codebook for MFCC descriptors."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import MiniBatchKMeans


class AudioCodebook:
    def __init__(
        self,
        size: int,
        random_state: int = 42,
        batch_size: int = 4096,
    ) -> None:
        if size <= 0 or batch_size <= 0:
            raise ValueError("Audio codebook parameters must be positive")

        self.size = size
        self.random_state = random_state
        self.batch_size = batch_size
        self.model = MiniBatchKMeans(
            n_clusters=size,
            random_state=random_state,
            batch_size=batch_size,
            n_init=3,
            reassignment_ratio=0.01,
        )

    def fit(self, descriptors: np.ndarray) -> None:
        """
        Train the acoustic codebook using MFCC descriptors.

        descriptors shape: (n_frames, n_mfcc)
        """
        if descriptors.ndim != 2:
            raise ValueError("MFCC descriptors must be a 2D array")

        if len(descriptors) < self.size:
            raise ValueError("Descriptor sample must contain at least codebook_size rows")

        descriptors = np.nan_to_num(descriptors, nan=0.0, posinf=0.0, neginf=0.0)

        self.model.fit(descriptors)

    def transform(self, descriptors: np.ndarray) -> np.ndarray:
        """
        Assign each MFCC descriptor to its nearest acoustic word.
        """
        if len(descriptors) == 0:
            return np.empty((0,), dtype=np.int32)

        if descriptors.ndim != 2:
            raise ValueError("MFCC descriptors must be a 2D array")

        descriptors = np.nan_to_num(descriptors, nan=0.0, posinf=0.0, neginf=0.0)

        return self.model.predict(descriptors).astype(np.int32, copy=False)

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(
            {
                "size": self.size,
                "random_state": self.random_state,
                "batch_size": self.batch_size,
                "model": self.model,
            },
            output,
        )

    @classmethod
    def load(cls, path: str | Path) -> "AudioCodebook":
        payload = joblib.load(path)

        codebook = cls(
            size=payload["size"],
            random_state=payload["random_state"],
            batch_size=payload["batch_size"],
        )

        codebook.model = payload["model"]

        return codebook