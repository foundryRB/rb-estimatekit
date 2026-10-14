"""Response DTO for project summary."""

from __future__ import annotations

from pydantic import BaseModel


class ProjectSummaryResponse(BaseModel):
    """Response for ``GET /api/projects/{slug}/summary``."""

    name: str
    client: str
    description: str
    phase_count: int
    requirement_count: int
    assumption_count: int
    archived: bool
    phases: list[str]
    """The defined phase ids in phase-table order; the slide deck is built for one of them."""
