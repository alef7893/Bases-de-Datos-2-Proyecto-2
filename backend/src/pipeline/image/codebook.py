"""K-Means visual codebook for SIFT descriptors."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import MiniBatchKMeans


class VisualCodebook:
    def __init__(
        self,
        size: int,
        random_state: int = 42,
        batch_size: int = 4096,
    ) -> None:
        if size <= 0 or batch_size <= 0:
            raise ValueError("Visual codebook parameters must be positive")
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
        if descriptors.ndim != 2 or descriptors.shape[1] != 128:
            raise ValueError("SIFT descriptors must have shape (n, 128)")
        if len(descriptors) < self.size:
            raise ValueError("Descriptor sample must contain at least codebook_size rows")
        self.model.fit(descriptors)

    def transform(self, descriptors: np.ndarray) -> np.ndarray:
        if len(descriptors) == 0:
            return np.empty((0,), dtype=np.int32)
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
    def load(cls, path: str | Path) -> "VisualCodebook":
        payload = joblib.load(path)
        codebook = cls(
            size=payload["size"],
            random_state=payload["random_state"],
            batch_size=payload["batch_size"],
        )
        codebook.model = payload["model"]
        return codebook
