"""Data preparation for the Architecture Guidelines workbook."""

from __future__ import annotations

from engine.domain.model.aggregates.project import Project

from .models import GroupSummary, GuidelineRow, GuidelinesData

__all__ = ["prepare_guidelines"]


def prepare_guidelines(project: Project) -> GuidelinesData | None:
    """Extract guideline data into plain structures. No openpyxl imports."""
    if not project.guidelines:
        return None

    grouped: dict[str, list[GuidelineRow]] = {}
    for g in project.guidelines:
        row = GuidelineRow(
            group=g.group,
            guideline_id=g.guideline_id,
            name=g.name,
            description=g.description,
            phase_ids=", ".join(sorted(g.phase_ids)),
        )
        grouped.setdefault(g.group, []).append(row)

    summaries: list[GroupSummary] = []
    for group_name, items in grouped.items():
        summaries.append(GroupSummary(
            group=group_name,
            count=len(items),
            names=", ".join(item.name for item in items),
        ))

    return GuidelinesData(
        project_name=project.config.name,
        total_count=len(project.guidelines),
        groups=list(grouped.items()),
        summaries=summaries,
    )
