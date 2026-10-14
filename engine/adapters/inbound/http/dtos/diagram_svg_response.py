"""Response DTO for a rendered architecture diagram."""

from __future__ import annotations

from pydantic import BaseModel


class DiagramSvgResponse(BaseModel):
    """Response for ``GET /api/projects/{slug}/architecture/diagrams/{name}``."""

    name: str
    svg: str
