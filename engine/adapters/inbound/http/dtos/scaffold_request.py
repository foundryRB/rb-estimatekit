"""Request DTO for project scaffolding."""

from __future__ import annotations

from pydantic import BaseModel


class ScaffoldRequest(BaseModel):
    """Body for ``POST /api/projects/scaffold``."""

    slug: str
    force: bool = False
