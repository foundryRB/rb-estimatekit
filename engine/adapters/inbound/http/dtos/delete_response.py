"""Response DTO for project deletion."""

from __future__ import annotations

from pydantic import BaseModel


class DeleteProjectResponse(BaseModel):
    """Response for ``DELETE /api/projects/{slug}``."""

    slug: str
    deleted: bool
