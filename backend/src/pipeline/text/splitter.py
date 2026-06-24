"""Split canonical product text into deterministic overlapping chunks."""

from __future__ import annotations

from src.common.models import Chunk, Modality, Product


class TextSplitter:
    def __init__(self, max_tokens: int = 128, overlap_tokens: int = 16) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if overlap_tokens < 0 or overlap_tokens >= max_tokens:
            raise ValueError("overlap_tokens must be between 0 and max_tokens - 1")
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def split(self, product: Product) -> list[Chunk]:
        words = product.canonical_text.split()
        if not words:
            return []

        chunks: list[Chunk] = []
        step = self.max_tokens - self.overlap_tokens
        for position, start in enumerate(range(0, len(words), step)):
            end = min(start + self.max_tokens, len(words))
            content = " ".join(words[start:end])
            if not content:
                break
            chunks.append(
                Chunk(
                    chunk_id=f"text:{product.product_id}:{position}",
                    product_id=product.product_id,
                    modality=Modality.TEXT,
                    position=position,
                    content=content,
                    metadata={
                        "start_token": start, 
                        "end_token": end,
                        "chunk_size": end - start,
                        "total_tokens": len(words)
                    }
                )
            )
            if end >= len(words):
                break
        return chunks
