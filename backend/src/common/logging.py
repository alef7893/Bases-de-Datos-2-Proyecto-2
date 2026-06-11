"""Project logging configuration."""

from __future__ import annotations

import logging

from .config import LoggingConfig


def configure_logging(config: LoggingConfig) -> None:
    """Configure root logging once using project settings."""

    logging.basicConfig(
        level=getattr(logging, config.level),
        format=config.format,
        force=True,
    )
