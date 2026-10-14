"""Response DTO for project archive and unarchive."""

from __future__ import annotations

from pydantic import BaseModel


class ArchiveProjectResponse(BaseModel):
    """Response for ``POST /api/projects/{slug}/archive`` and ``.../unarchive``."""

    slug: str
    archived: bool
