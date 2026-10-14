"""SlideNote — a positioned text snippet for a specific slide."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["SlideNote"]


@dataclass
class SlideNote:
    """A positioned text snippet for a specific slide.

    Loaded from Slide-Notes.tsv. Each note targets a slide and a position
    (e.g., slide="architecture", position="subtitle").
    """

    slide: str          # Generator / slide identifier
    position: str       # Slot within the slide
    text: str
