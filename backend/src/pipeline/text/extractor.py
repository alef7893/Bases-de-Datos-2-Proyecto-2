"""Tokenization, stopword removal, and stemming for English product text."""

from __future__ import annotations

import re

from nltk.stem import PorterStemmer, SnowballStemmer

from src.common.models import Chunk


ENGLISH_STOPWORDS = frozenset(
    """
    a an and are as at be been being by for from has have he her hers him his
    i in into is it its of on or our ours she that the their theirs them they
    this those to was we were what when where which who will with you your
    yours product products buy use using
    """.split()
)


class TextFeatureExtractor:
    TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")

    def __init__(
        self,
        lowercase: bool = True,
        remove_stopwords: bool = True,
        stemmer: str = "porter",
    ) -> None:
        self.lowercase = lowercase
        self.remove_stopwords = remove_stopwords
        if stemmer == "porter":
            self._stemmer = PorterStemmer()
        elif stemmer == "snowball":
            self._stemmer = SnowballStemmer("english")
        elif stemmer == "none":
            self._stemmer = None
        else:
            raise ValueError(f"Unsupported stemmer: {stemmer}")

    def extract_text(self, text: str) -> list[str]:
        normalized = text.lower() if self.lowercase else text
        tokens = self.TOKEN_PATTERN.findall(normalized)
        if self.remove_stopwords:
            tokens = [token for token in tokens if token not in ENGLISH_STOPWORDS]
        if self._stemmer is not None:
            tokens = [self._stemmer.stem(token) for token in tokens]
        return tokens

    def extract(self, chunk: Chunk) -> list[str]:
        return self.extract_text(chunk.content or "")
