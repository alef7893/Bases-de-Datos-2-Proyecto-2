"""Metrics shared by Phase 3 comparison scripts."""

from __future__ import annotations

from collections.abc import Sequence
from statistics import mean, median

from src.common.models import SearchResult


def recall_at_k(
    results: Sequence[SearchResult],
    reference: Sequence[SearchResult],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    relevant = {result.product_id for result in reference[:k]}
    if not relevant:
        return 1.0 if not results else 0.0
    retrieved = {result.product_id for result in results[:k]}
    return len(retrieved & relevant) / len(relevant)


def precision_at_k(
    results: Sequence[SearchResult],
    relevant_product_ids: set[int],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    selected = results[:k]
    if not selected:
        return 0.0
    return sum(result.product_id in relevant_product_ids for result in selected) / len(
        selected
    )


def latency_summary(values: Sequence[float]) -> dict[str, float]:
    if not values:
        raise ValueError("at least one latency value is required")
    ordered = sorted(float(value) for value in values)
    p95_index = min(len(ordered) - 1, max(0, round(0.95 * len(ordered) + 0.5) - 1))
    return {
        "mean_ms": mean(ordered),
        "median_ms": median(ordered),
        "p95_ms": ordered[p95_index],
        "min_ms": ordered[0],
        "max_ms": ordered[-1],
    }
