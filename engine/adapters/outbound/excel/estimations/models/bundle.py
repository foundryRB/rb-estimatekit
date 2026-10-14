"""Bundle type wrapping all estimation sheet data."""

from __future__ import annotations

from dataclasses import dataclass, field

from .build import BuildGroupData
from .estimate import EstimateRow


@dataclass
class EstimationData:
    """All prepared data for one phase estimation workbook."""

    phase_name: str
    phase_id: str
    build_groups: list[BuildGroupData] = field(default_factory=list)
    build_total: float = 0.0
    estimate_rows: list[EstimateRow] = field(default_factory=list)
    authored_total: float = 0.0     # sum of the estimate rows
    staffed_capacity: float = 0.0   # what the resource plan books
