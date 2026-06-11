"""Search the custom text index from the command line."""

from __future__ import annotations

import argparse
import json

from src.common.config import load_project_config
from src.common.models import Modality, Query
from src.multimodal.stage_06_similarity_search.text_retriever import TextRetriever
from src.multimodal.stage_04_codebook.text_codebook import TextCodebook
from src.multimodal.stage_03_extractor_features.text_extractor import TextFeatureExtractor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--scale", choices=("1k", "10k", "full"), default=None)
    parser.add_argument("--top-k", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_project_config()
    scale = args.scale or config.data.active_scale
    output_dir = config.paths.artifacts_dir / "text" / scale
    extractor = TextFeatureExtractor(
        lowercase=config.text.lowercase,
        remove_stopwords=config.text.remove_stopwords,
        stemmer=config.text.stemmer,
    )
    retriever = TextRetriever(
        output_dir / "index",
        TextCodebook.load(output_dir / "codebook.json"),
        extractor,
    )
    results = retriever.search(
        Query(modality=Modality.TEXT, text=args.query),
        top_k=args.top_k,
    )
    print(json.dumps([result.model_dump(mode="json") for result in results], indent=2))


if __name__ == "__main__":
    main()



