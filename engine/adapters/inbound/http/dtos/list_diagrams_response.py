"""Response DTO for listing architecture diagrams."""

from __future__ import annotations

from pydantic import BaseModel


class DiagramInfoItem(BaseModel):
    """Single architecture diagram entry."""

    name: str
    path: str


class ListDiagramsResponse(BaseModel):
    """Response for ``GET /api/projects/{slug}/architecture/diagrams``."""

    diagrams: list[DiagramInfoItem]
