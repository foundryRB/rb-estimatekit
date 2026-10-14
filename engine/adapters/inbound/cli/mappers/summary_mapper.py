"""Mapper: domain ProjectSummary to CLI SummaryView."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.adapters.inbound.cli.dtos.summary_view import SummaryView

if TYPE_CHECKING:
    from engine.domain.model.value_objects.project_summary import ProjectSummary


def map_summary(summary: ProjectSummary) -> SummaryView:
    """Map a domain ProjectSummary to a CLI SummaryView."""
    return SummaryView(
        name=summary.name,
        client=summary.client,
        description=summary.description,
        phase_count=summary.phase_count,
        requirement_count=summary.requirement_count,
        assumption_count=summary.assumption_count,
        phases=list(summary.phases),
    )
