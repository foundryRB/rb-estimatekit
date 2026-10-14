"""Bundle type wrapping all requirements sheet data."""

from __future__ import annotations

from dataclasses import dataclass, field

from .category_summary import CategorySummaryRow
from .requirements import ReqMatrixRow
from .summary import EffortRow, PhaseOverviewRow


@dataclass
class RequirementsData:
    """All prepared data for the requirements workbook."""

    project_name: str
    project_description: str
    total_reqs: int
    phase_names: list[str]  # display names for header columns
    phase_ids: list[str]  # matching IDs
    phase_overview: list[PhaseOverviewRow] = field(default_factory=list)
    effort_rows: list[EffortRow] = field(default_factory=list)
    grand_build: float = 0.0
    grand_overhead: float = 0.0
    grand_total: float = 0.0
    categories: list[str] = field(default_factory=list)  # display names in order
    req_groups: list[tuple[str, list[ReqMatrixRow]]] = field(default_factory=list)
    category_summaries: list[CategorySummaryRow] = field(default_factory=list)
