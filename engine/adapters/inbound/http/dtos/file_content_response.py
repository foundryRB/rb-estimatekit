"""Response DTO for reading a single project file."""

from __future__ import annotations

from pydantic import BaseModel


class FileContentResponse(BaseModel):
    """Response for ``GET /api/projects/{slug}/files/{path}``."""

    path: str
    content: str
