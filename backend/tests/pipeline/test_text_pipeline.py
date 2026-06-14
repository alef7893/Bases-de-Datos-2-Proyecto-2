from pathlib import Path

from src.common.models import Modality, Product, Query
from src.retrieval.custom.text.inverted_index import SPIMIIndexer
from src.retrieval.custom.text.retriever import TextRetriever
from src.pipeline.text.codebook import TextCodebook
from src.pipeline.text.extractor import TextFeatureExtractor
from src.pipeline.text.splitter import TextSplitter


def test_text_splitter_creates_overlapping_chunks() -> None:
    product = Product(product_id=1, canonical_text="one two three four five six")
    splitter = TextSplitter(max_tokens=4, overlap_tokens=2)

    chunks = splitter.split(product)

    assert [chunk.content for chunk in chunks] == [
        "one two three four",
        "three four five six",
    ]


def test_extractor_normalizes_stopwords_and_stems() -> None:
    extractor = TextFeatureExtractor(stemmer="porter")

    assert extractor.extract_text("The running shoes are BLACK") == [
        "run",
        "shoe",
        "black",
    ]


def test_codebook_vectors_are_normalized(tmp_path: Path) -> None:
    codebook = TextCodebook(max_terms=10, min_document_frequency=1)
    codebook.fit([["black", "shoe"], ["black", "bag"]])

    vector = codebook.transform(["black", "black", "shoe"])
    codebook.save(tmp_path / "codebook.json")
    loaded = TextCodebook.load(tmp_path / "codebook.json")

    assert abs(sum(value * value for value in vector.values()) - 1.0) < 1e-9
    assert loaded.terms == codebook.terms


def test_spimi_and_retriever_return_ranked_products(tmp_path: Path) -> None:
    extractor = TextFeatureExtractor(stemmer="none")
    splitter = TextSplitter()
    products = [
        Product(product_id=1, canonical_text="black sports shoes"),
        Product(product_id=2, canonical_text="red casual handbag"),
        Product(product_id=3, canonical_text="black casual shoes"),
    ]
    chunks = [chunk for product in products for chunk in splitter.split(product)]
    features = {chunk.chunk_id: extractor.extract(chunk) for chunk in chunks}
    codebook = TextCodebook(max_terms=20, min_document_frequency=1)
    codebook.fit(features.values())
    indexer = SPIMIIndexer(tmp_path / "index", max_postings_per_block=2)

    summary = indexer.build(
        (chunk, codebook.transform(features[chunk.chunk_id])) for chunk in chunks
    )
    retriever = TextRetriever(tmp_path / "index", codebook, extractor)
    results = retriever.search(
        Query(modality=Modality.TEXT, text="black shoes"),
        top_k=2,
    )

    assert summary["blocks"] > 1
    assert [result.product_id for result in results] == [3, 1]
    assert results[0].score > results[1].score





