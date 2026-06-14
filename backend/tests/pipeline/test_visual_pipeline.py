from pathlib import Path

import cv2
import numpy as np

from src.common.models import Modality, Query
from src.retrieval.custom.image.inverted_index import VisualInvertedIndexer
from src.retrieval.custom.image.retriever import VisualRetriever
from src.pipeline.image.codebook import VisualCodebook
from src.pipeline.image.histogram import build_visual_histogram, sparse_visual_histogram
from src.pipeline.image.preprocessing import load_grayscale_image
from src.pipeline.image.sift_extractor import SIFTExtractor


def _write_feature_image(path: Path, offset: int = 0) -> None:
    image = np.zeros((240, 320), dtype=np.uint8)
    cv2.rectangle(image, (40 + offset, 40), (200 + offset, 180), 255, 4)
    cv2.circle(image, (120 + offset, 110), 45, 180, 3)
    cv2.line(image, (20, 220), (300, 20), 220, 3)
    assert cv2.imwrite(str(path), image)


def test_image_preprocessing_and_sift_checkpoint(tmp_path: Path) -> None:
    image_path = tmp_path / "image.jpg"
    _write_feature_image(image_path)
    image = load_grayscale_image(image_path, max_width=160, max_height=120)
    extractor = SIFTExtractor(160, 120, 100)

    first = extractor.extract_with_checkpoint(1, image_path, tmp_path / "descriptors")
    second = extractor.extract_with_checkpoint(1, image_path, tmp_path / "descriptors")

    assert image.shape[0] <= 120 and image.shape[1] <= 160
    assert first.shape[1] == 128
    assert np.array_equal(first, second)


def test_visual_codebook_histogram_index_and_retrieval(tmp_path: Path) -> None:
    rng = np.random.default_rng(42)
    training = rng.normal(size=(100, 128)).astype(np.float32)
    codebook = VisualCodebook(size=4, random_state=42, batch_size=16)
    codebook.fit(training)
    histogram_a = build_visual_histogram(codebook.transform(training[:30]), 4)
    histogram_b = build_visual_histogram(codebook.transform(training[70:]), 4)
    VisualInvertedIndexer(tmp_path / "index").build(
        [
            (1, sparse_visual_histogram(histogram_a)),
            (2, sparse_visual_histogram(histogram_b)),
        ]
    )

    class FakeExtractor:
        def extract_path(self, path):
            return training[:30]

    retriever = VisualRetriever(tmp_path / "index", codebook, FakeExtractor())
    results = retriever.search(
        Query(modality=Modality.IMAGE, image_path=tmp_path / "query.jpg"),
        top_k=2,
    )

    assert results[0].product_id == 1
    assert results[0].score >= results[1].score





