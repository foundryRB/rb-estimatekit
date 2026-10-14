"""Mapper for discover-projects responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.adapters.inbound.http.dtos.discover_response import DiscoverProjectsResponse

if TYPE_CHECKING:
    from engine.domain.model.value_objects.discovered_project import DiscoveredProject


def map_discover_response(entries: list[DiscoveredProject]) -> DiscoverProjectsResponse:
    """Map discovered projects to the response DTO.

    Returns the project directory *name* (slug), not the full path.
    The frontend identifies projects by slug, not by filesystem path.
    Active and archived slugs are reported separately, so callers that
    join on ``projects`` never see parked work.
    """
    return DiscoverProjectsResponse(
        projects=[e.path.name for e in entries if not e.archived],
        archived=[e.path.name for e in entries if e.archived],
    )
