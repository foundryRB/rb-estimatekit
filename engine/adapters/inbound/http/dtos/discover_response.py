"""Response DTO for project discovery."""

from __future__ import annotations

from pydantic import BaseModel


class DiscoverProjectsResponse(BaseModel):
    """Response for ``GET /api/projects/``.

    ``projects`` lists the active slugs; ``archived`` lists the parked ones,
    so archived work stays visible without answering in the default listing.
    """

    projects: list[str]
    archived: list[str]
