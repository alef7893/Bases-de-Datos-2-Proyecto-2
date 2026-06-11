"""Text and metadata cleaning helpers for the fashion dataset."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Any, Iterable


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    parser = _TextExtractor()
    parser.feed(html.unescape(value))
    parser.close()
    return normalize_whitespace(" ".join(parser.parts))


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    text = normalize_whitespace(str(value))
    return "" if text.lower() in {"na", "n/a", "none", "null"} else text


def flatten_attribute_values(attributes: Any) -> list[str]:
    if not isinstance(attributes, dict):
        return []
    values: list[str] = []
    for key, value in attributes.items():
        normalized_key = normalize_value(key)
        normalized_value = normalize_value(value)
        if normalized_key:
            values.append(normalized_key)
        if normalized_value:
            values.append(normalized_value)
    return values


def build_canonical_text(parts: Iterable[str]) -> str:
    cleaned = [normalize_value(part) for part in parts]
    return normalize_whitespace(" ".join(part for part in cleaned if part))


def safe_slug(value: str) -> str:
    """Create a stable lowercase label useful for grouping."""

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"
