"""Text codebook selection and sparse TF-IDF vectorization."""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Iterable, Sequence
from pathlib import Path

class TextCodebook:
    def __init__(self, max_terms: int, min_document_frequency: int = 2) -> None:
        if max_terms <= 0 or min_document_frequency <= 0:
            raise ValueError("codebook parameters must be positive")
        self.max_terms = max_terms
        self.min_document_frequency = min_document_frequency
        self.document_count = 0
        self.terms: list[str] = []
        self.idf: dict[str, float] = {}

    def fit(self, documents: Iterable[Sequence[str]]) -> None:
        term_frequency: Counter[str] = Counter()
        document_frequency: Counter[str] = Counter()
        document_count = 0

        for tokens in documents:
            document_count += 1
            term_frequency.update(tokens)
            document_frequency.update(set(tokens))

        eligible = [
            term
            for term, frequency in term_frequency.items()
            if document_frequency[term] >= self.min_document_frequency
        ]
        eligible.sort(key=lambda term: (-term_frequency[term], term))
        self.terms = eligible[: self.max_terms]
        self.document_count = document_count
        self.idf = {
            term: math.log(
                (1 + document_count) / (1 + document_frequency[term])
            )
            + 1.0
            for term in self.terms
        }

    def transform(self, tokens: Sequence[str]) -> dict[str, float]:
        counts = Counter(token for token in tokens if token in self.idf)
        weights = {
            term: (1.0 + math.log(count)) * self.idf[term]
            for term, count in counts.items()
        }
        norm = math.sqrt(sum(weight * weight for weight in weights.values()))
        if norm:
            return {term: weight / norm for term, weight in weights.items()}
        return {}
    
    def transform_batch(self, documents: Iterable[Sequence[str]]) -> list[dict[str, float]]:
        if not self._fitted:
            raise RuntimeError("codebook must be fitted before transforming documents")
        return [self.transform(tokens) for tokens in documents]

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "max_terms": self.max_terms,
            "min_document_frequency": self.min_document_frequency,
            "document_count": self.document_count,
            "terms": self.terms,
            "idf": self.idf,
        }
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "TextCodebook":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        codebook = cls(
            max_terms=payload["max_terms"],
            min_document_frequency=payload["min_document_frequency"],
        )
        codebook.document_count = payload["document_count"]
        codebook.terms = payload["terms"]
        codebook.idf = {term: float(value) for term, value in payload["idf"].items()}
        return codebook
