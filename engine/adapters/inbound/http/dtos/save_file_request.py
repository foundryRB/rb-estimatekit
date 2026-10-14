"""Request DTO for saving a project file."""

from __future__ import annotations

from pydantic import BaseModel


class SaveFileRequest(BaseModel):
    """Request body for ``PUT /api/projects/{slug}/files/{path}``."""

    content: str
