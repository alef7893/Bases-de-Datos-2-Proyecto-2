"""Weighted late fusion for rankings returned by independent retrievers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from src.common.models import Modality, SearchResult

from .ranking import max_normalize


class WeightedScoreFusion:
    def __init__(self, weights: Mapping[Modality | str, float]) -> None:
        normalized = {
            Modality(key) if isinstance(key, str) else key: float(value)
            for key, value in weights.items()
        }
        if any(value < 0 for value in normalized.values()):
            raise ValueError("fusion weights cannot be negative")
        total = sum(normalized.values())
        if total <= 0:
            raise ValueError("at least one fusion weight must be positive")
        self.weights = {key: value / total for key, value in normalized.items()}

    def fuse(
        self,
        rankings: Mapping[Modality, Sequence[SearchResult]],
        top_k: int,
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        normalized = {
            modality: max_normalize(results) for modality, results in rankings.items()
        }
        product_ids = set().union(*(scores.keys() for scores in normalized.values()))
        fused: list[tuple[int, float, dict[str, float]]] = []
        for product_id in product_ids:
            modality_scores = {
                modality.value: normalized.get(modality, {}).get(product_id, 0.0)
                for modality in self.weights
            }
            score = sum(
                self.weights[modality] * modality_scores[modality.value]
                for modality in self.weights
            )
            fused.append((product_id, score, modality_scores))

        fused.sort(key=lambda item: (-item[1], item[0]))
        return [
            SearchResult(
                product_id=product_id,
                score=score,
                rank=rank,
                modality=Modality.MULTIMODAL,
                metadata={"modality_scores": modality_scores},
            )
            for rank, (product_id, score, modality_scores) in enumerate(
                fused[:top_k], start=1
            )
        ]
