"""Extract SIFT, train visual codebook, and build the visual inverted index."""

from __future__ import annotations

import argparse
import json

import numpy as np

from src.common.config import load_project_config
from src.multimodal.stage_01_content.loader import read_catalog
from src.multimodal.stage_05_inverted_index.visual_index import VisualInvertedIndexer
from src.multimodal.stage_04_codebook.visual_codebook import VisualCodebook
from src.multimodal.stage_04_codebook.visual_histogram import build_visual_histogram, sparse_visual_histogram
from src.multimodal.stage_03_extractor_features.sift_extractor import SIFTExtractor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    return parser.parse_args()


def _sample_descriptors(
    descriptor_arrays: list[np.ndarray], sample_size: int, seed: int
) -> np.ndarray:
    available = sum(len(array) for array in descriptor_arrays)
    if available == 0:
        raise ValueError("No SIFT descriptors were extracted from training images")
    target = min(sample_size, available)
    rng = np.random.default_rng(seed)
    quotas = [
        min(len(array), max(1, round(target * len(array) / available)))
        for array in descriptor_arrays
    ]
    samples: list[np.ndarray] = []
    for array, quota in zip(descriptor_arrays, quotas, strict=True):
        if quota >= len(array):
            samples.append(array)
        else:
            samples.append(array[rng.choice(len(array), size=quota, replace=False)])
    combined = np.vstack(samples)
    if len(combined) > target:
        combined = combined[rng.choice(len(combined), size=target, replace=False)]
    return combined.astype(np.float32, copy=False)


def main() -> None:
    args = parse_args()
    config = load_project_config()
    scale = args.scale or config.data.active_scale
    manifest = json.loads(
        (config.paths.artifacts_dir / "partitions" / f"{scale}.json").read_text(
            encoding="utf-8"
        )
    )
    selected_ids = set().union(*manifest["splits"].values())
    train_ids = set(manifest["splits"]["train"])
    products = [
        product
        for product in read_catalog(config.paths.artifacts_dir / "catalog" / "products.jsonl")
        if product.product_id in selected_ids and product.has_image
    ]

    output_dir = config.paths.artifacts_dir / "vision" / scale
    descriptors_dir = output_dir / "descriptors"
    histograms_dir = output_dir / "histograms"
    histograms_dir.mkdir(parents=True, exist_ok=True)
    extractor = SIFTExtractor(
        max_width=config.vision.max_image_width,
        max_height=config.vision.max_image_height,
        max_keypoints=config.vision.max_keypoints_per_image,
    )

    descriptors_by_product: dict[int, np.ndarray] = {}
    for product in products:
        descriptors_by_product[product.product_id] = extractor.extract_with_checkpoint(
            product.product_id,
            product.image_path,
            descriptors_dir,
        )

    training_descriptors = _sample_descriptors(
        [
            descriptors_by_product[product.product_id]
            for product in products
            if product.product_id in train_ids
            and len(descriptors_by_product[product.product_id])
        ],
        sample_size=config.vision.descriptor_sample_size,
        seed=config.vision.random_state,
    )
    codebook = VisualCodebook(
        size=config.vision.codebook_size,
        random_state=config.vision.random_state,
    )
    codebook.fit(training_descriptors)
    codebook_path = output_dir / "codebook.joblib"
    codebook.save(codebook_path)

    sparse_histograms: list[tuple[int, dict[int, float]]] = []
    empty_products = 0
    for product in products:
        descriptors = descriptors_by_product[product.product_id]
        histogram = build_visual_histogram(
            codebook.transform(descriptors), codebook.size
        )
        np.save(histograms_dir / f"{product.product_id}.npy", histogram)
        sparse = sparse_visual_histogram(histogram)
        if not sparse:
            empty_products += 1
        sparse_histograms.append((product.product_id, sparse))

    summary = VisualInvertedIndexer(output_dir / "index").build(sparse_histograms)
    summary.update(
        {
            "scale": scale,
            "products_with_image": len(products),
            "empty_products": empty_products,
            "training_descriptor_sample": len(training_descriptors),
            "codebook_size": codebook.size,
            "codebook": str(codebook_path),
        }
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()



