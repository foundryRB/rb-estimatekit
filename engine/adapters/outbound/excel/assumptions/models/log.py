"""Data shapes for the Assumptions Log sheet."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["AssumptionRow", "LegendDef", "LogData"]


@dataclass(frozen=True)
class LegendDef:
    """A single legend entry (confidence or impact definition)."""

    level: str
    description: str


@dataclass(frozen=True)
class AssumptionRow:
    """Flat representation of one assumption for the Log sheet."""

    assumption_id: str
    group: str
    assumption: str
    confidence: str
    impact: str
    req_ids_str: str


@dataclass
class LogData:
    """Pre-computed data for the Assumptions Log sheet."""

    project_name: str
    conf_defs: list[LegendDef]
    impact_defs: list[LegendDef]
    groups: list[str]
    grouped_rows: dict[str, list[AssumptionRow]] = field(default_factory=dict)
