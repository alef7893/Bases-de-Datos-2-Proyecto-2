"""Shared ranking helpers."""

from __future__ import annotations

from collections.abc import Sequence

from src.common.models import SearchResult


def max_normalize(results: Sequence[SearchResult]) -> dict[int, float]:
    if not results:
        return {}
    maximum = max(result.score for result in results)
    if maximum <= 0:
        return {result.product_id: 0.0 for result in results}
    return {result.product_id: result.score / maximum for result in results}
