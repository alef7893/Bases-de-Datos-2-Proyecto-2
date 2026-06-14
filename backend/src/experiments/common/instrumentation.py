"""Resource and PostgreSQL-plan instrumentation shared by evaluators."""

from __future__ import annotations

import sys
import tracemalloc
from time import perf_counter
from typing import Callable

from src.common.models import SearchResult


def summarize_plan_io(plan: dict) -> dict[str, float]:
    totals = {
        "shared_hit_blocks": 0,
        "shared_read_blocks": 0,
        "shared_dirtied_blocks": 0,
        "shared_written_blocks": 0,
        "io_read_time_ms": 0.0,
        "io_write_time_ms": 0.0,
    }

    def visit(node: dict) -> None:
        mapping = {
            "Shared Hit Blocks": "shared_hit_blocks",
            "Shared Read Blocks": "shared_read_blocks",
            "Shared Dirtied Blocks": "shared_dirtied_blocks",
            "Shared Written Blocks": "shared_written_blocks",
            "I/O Read Time": "io_read_time_ms",
            "I/O Write Time": "io_write_time_ms",
        }
        for source, target in mapping.items():
            totals[target] += node.get(source, 0)
        for child in node.get("Plans", []):
            visit(child)

    visit(plan["Plan"])
    totals["execution_time_ms"] = float(plan.get("Execution Time", 0))
    totals["planning_time_ms"] = float(plan.get("Planning Time", 0))
    return totals


def deep_size(value, seen: set[int] | None = None) -> int:
    seen = seen or set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(
            deep_size(key, seen) + deep_size(item, seen)
            for key, item in value.items()
        )
    elif isinstance(value, (list, tuple, set, frozenset)):
        size += sum(deep_size(item, seen) for item in value)
    return size


def timed(
    call: Callable[[], list[SearchResult]],
) -> tuple[list[SearchResult], float]:
    started = perf_counter()
    results = call()
    return results, (perf_counter() - started) * 1000


def peak_python_bytes(call: Callable[[], object]) -> int:
    tracemalloc.start()
    call()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak
