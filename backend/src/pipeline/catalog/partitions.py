"""Create deterministic, group-aware, approximately stratified partitions."""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from src.common.models import Product


def _group_id(product: Product) -> str:
    return product.duplicate_image_group or f"product:{product.product_id}"


def _stratum(product: Product) -> str:
    return product.categories.get("masterCategory", "Unknown")


def _stable_seed(seed: int, value: str) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _build_groups(products: Iterable[Product]) -> list[list[Product]]:
    groups: dict[str, list[Product]] = defaultdict(list)
    for product in products:
        groups[_group_id(product)].append(product)
    return list(groups.values())


def _ordered_groups(products: Iterable[Product], seed: int) -> list[list[Product]]:
    strata: dict[str, list[list[Product]]] = defaultdict(list)
    for group in _build_groups(products):
        strata[_stratum(group[0])].append(group)

    for name, groups in strata.items():
        random.Random(_stable_seed(seed, name)).shuffle(groups)

    ordered: list[list[Product]] = []
    names = sorted(strata)
    while names:
        next_names: list[str] = []
        for name in names:
            groups = strata[name]
            if groups:
                ordered.append(groups.pop())
            if groups:
                next_names.append(name)
        names = next_names
    return ordered


def select_products(
    products: Iterable[Product], target_size: int | None, seed: int
) -> list[Product]:
    ordered = _ordered_groups(products, seed)
    selected: list[Product] = []
    for group in ordered:
        if target_size is not None and len(selected) >= target_size:
            break
        selected.extend(group)
    return selected


def split_products(
    products: Iterable[Product], ratios: dict[str, float], seed: int
) -> dict[str, list[int]]:
    groups = _ordered_groups(products, seed)
    total = sum(len(group) for group in groups)
    targets = {name: total * ratio for name, ratio in ratios.items()}
    splits: dict[str, list[int]] = {name: [] for name in ratios}

    for group in groups:
        destination = min(
            ratios,
            key=lambda name: len(splits[name]) / targets[name]
            if targets[name]
            else float("inf"),
        )
        splits[destination].extend(product.product_id for product in group)

    for values in splits.values():
        values.sort()
    return splits


def build_partition_manifests(
    products: Iterable[Product],
    partition_sizes: dict[str, int | None],
    split_ratios: dict[str, float],
    output_dir: str | Path,
    seed: int,
) -> dict[str, Path]:
    all_products = list(products)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    for name, size in partition_sizes.items():
        selected = select_products(all_products, size, seed)
        splits = split_products(selected, split_ratios, seed)
        payload = {
            "name": name,
            "seed": seed,
            "requested_size": size,
            "actual_size": len(selected),
            "split_ratios": split_ratios,
            "splits": splits,
        }
        path = output / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written[name] = path
    return written
