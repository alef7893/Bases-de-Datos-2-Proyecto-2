"""Helpers for sparse text histograms."""

from __future__ import annotations

from collections.abc import Mapping
import math

def sparse_dot(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(term, 0.0) for term, value in left.items())

def sparse_norm(vector: Mapping[str, float]) -> float:
    return math.sqrt(sum(v * v for v in vector.values()))

def cosine_similarity(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    dot = sparse_dot(left, right)
    if dot == 0.0:
        return 0.0
    norm_left = sparse_norm(left)
    norm_right = sparse_norm(right)
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)
