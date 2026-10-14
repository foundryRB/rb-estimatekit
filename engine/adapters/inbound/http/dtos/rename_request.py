"""Request DTO for project rename."""

from __future__ import annotations

from pydantic import BaseModel


class RenameRequest(BaseModel):
    """Request body for ``POST /api/projects/{slug}/rename``."""

    new_slug: str | None = None
    new_name: str | None = None
