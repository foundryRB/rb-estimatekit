"""Port: diagram renderer - turn diagram source text into an SVG document."""

from __future__ import annotations

from typing import Protocol

__all__ = ["DiagramRenderer"]


class DiagramRenderer(Protocol):
    """Rendering contract for architecture diagram sources.

    Use cases depend on this protocol; outbound adapters implement it.
    Implementations MUST render locally: a client's architecture is
    confidential, so the diagram source never leaves the process boundary
    (never a third-party rendering server).
    """

    def render_svg(self, source: str) -> str:
        """Render diagram source text to an SVG document.

        Raises DiagramRenderError when the source cannot be rendered.
        """
        ...
