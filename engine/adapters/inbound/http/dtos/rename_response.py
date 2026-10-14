"""Response DTO for project rename."""

from __future__ import annotations

from pydantic import BaseModel


class RenameProjectResponse(BaseModel):
    """Response for ``POST /api/projects/{slug}/rename``."""

    slug: str
    new_slug: str
    renamed: bool
