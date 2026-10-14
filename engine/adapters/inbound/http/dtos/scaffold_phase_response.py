"""Response DTO for minting a phase."""

from __future__ import annotations

from pydantic import BaseModel


class ScaffoldPhaseResponse(BaseModel):
    """Response for ``POST /api/projects/{slug}/phases/{phase_id}``."""

    slug: str
    phase_id: str
    files: list[str]
    """The project-relative paths written, every example value sentinel-marked."""
