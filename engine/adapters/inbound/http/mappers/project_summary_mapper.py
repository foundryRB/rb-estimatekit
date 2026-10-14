"""Mapper for project-summary responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.adapters.inbound.http.dtos.project_summary_response import ProjectSummaryResponse

if TYPE_CHECKING:
    from engine.domain.model.value_objects.project_summary import ProjectSummary


def map_project_summary_response(summary: ProjectSummary) -> ProjectSummaryResponse:
    """Map a domain ProjectSummary to the response DTO."""
    return ProjectSummaryResponse(
        name=summary.name,
        client=summary.client,
        description=summary.description,
        phase_count=summary.phase_count,
        requirement_count=summary.requirement_count,
        assumption_count=summary.assumption_count,
        archived=summary.archived,
        phases=list(summary.phases),
    )
