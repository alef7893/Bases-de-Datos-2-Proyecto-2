"""Build the custom TF-IDF codebook and SPIMI text index."""

from __future__ import annotations

import argparse
import json

from src.common.config import load_project_config
from src.common.logging import configure_logging
from src.multimodal.stage_01_content.loader import read_catalog
from src.multimodal.stage_05_inverted_index.spimi import SPIMIIndexer
from src.multimodal.stage_04_codebook.text_codebook import TextCodebook
from src.multimodal.stage_03_extractor_features.text_extractor import TextFeatureExtractor
from src.multimodal.stage_02_split_chunks.text_splitter import TextSplitter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_project_config()
    configure_logging(config.logging)
    scale = args.scale or config.data.active_scale

    manifest_path = config.paths.artifacts_dir / "partitions" / f"{scale}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected_ids = set().union(*manifest["splits"].values())
    train_ids = set(manifest["splits"]["train"])
    products = [
        product
        for product in read_catalog(config.paths.artifacts_dir / "catalog" / "products.jsonl")
        if product.product_id in selected_ids
    ]

    splitter = TextSplitter(
        max_tokens=config.text.chunk_max_tokens,
        overlap_tokens=config.text.chunk_overlap_tokens,
    )
    extractor = TextFeatureExtractor(
        lowercase=config.text.lowercase,
        remove_stopwords=config.text.remove_stopwords,
        stemmer=config.text.stemmer,
    )
    chunks = [chunk for product in products for chunk in splitter.split(product)]
    features = {chunk.chunk_id: extractor.extract(chunk) for chunk in chunks}

    codebook = TextCodebook(
        max_terms=config.text.codebook_size,
        min_document_frequency=config.text.min_document_frequency,
    )
    codebook.fit(
        features[chunk.chunk_id] for chunk in chunks if chunk.product_id in train_ids
    )

    output_dir = config.paths.artifacts_dir / "text" / scale
    codebook_path = output_dir / "codebook.json"
    codebook.save(codebook_path)
    indexer = SPIMIIndexer(
        output_dir / "index",
        max_postings_per_block=config.text.spimi_max_postings_per_block,
    )
    summary = indexer.build(
        (chunk, codebook.transform(features[chunk.chunk_id])) for chunk in chunks
    )
    summary.update(
        {
            "scale": scale,
            "products": len(products),
            "codebook_terms": len(codebook.terms),
            "training_documents": codebook.document_count,
            "codebook": str(codebook_path),
        }
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()



