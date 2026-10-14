"""Pipeline — generation pipeline types."""

from __future__ import annotations

from enum import StrEnum

__all__ = ["Pipeline"]


class Pipeline(StrEnum):
    """The generation pipelines supported by the engine."""

    ROADMAP = "roadmap"
    EXCEL = "excel"
    SLIDES = "slides"
