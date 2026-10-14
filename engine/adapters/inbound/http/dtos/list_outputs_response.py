"""Response DTO for listing generated output files."""

from __future__ import annotations

from pydantic import BaseModel


class OutputFileItem(BaseModel):
    """Single output file entry."""

    name: str
    pipeline: str
    path: str
    size: int


class ListOutputsResponse(BaseModel):
    """Response for ``GET /api/projects/{slug}/outputs``."""

    outputs: list[OutputFileItem]
