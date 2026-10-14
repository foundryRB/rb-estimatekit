"""Response DTO for project scaffolding."""

from __future__ import annotations

from pydantic import BaseModel


class ScaffoldProjectResponse(BaseModel):
    """Response for ``POST /api/projects/scaffold``."""

    slug: str
    path: str
