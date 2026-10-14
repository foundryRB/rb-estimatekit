"""Bundle type wrapping all guidelines sheet data."""

from __future__ import annotations

from dataclasses import dataclass

from .overview import GuidelineRow
from .summary import GroupSummary

__all__ = ["GuidelinesData"]


@dataclass(frozen=True)
class GuidelinesData:
    """All prepared data for the guidelines workbook."""

    project_name: str
    total_count: int
    groups: list[tuple[str, list[GuidelineRow]]]  # (group_name, rows) in order
    summaries: list[GroupSummary]
