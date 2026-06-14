"""Central registry controlling available frontend applications and their order."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .app01_visual_search import render
from .app04_multimodal_recommender import render as render_app04


@dataclass(frozen=True)
class FrontendApplication:
    application_id: str
    label: str
    render: Callable[[Any, list[Any]], None]


APPLICATIONS = (
    FrontendApplication("app01", "App 01 - Busqueda visual", render),
    FrontendApplication("app04", "App 04 - Recomendacion multimodal", render_app04),
)
