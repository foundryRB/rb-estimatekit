"""Data shapes for the Traceability sheet."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["TraceRow", "TraceabilityData"]


@dataclass(frozen=True)
class TraceRow:
    """Traceability row: one requirement and its linked assumptions."""

    req_id: str
    count: int
    assumption_ids_str: str
    worst_confidence: str
    worst_impact: str


@dataclass
class TraceabilityData:
    """Pre-computed data for the Traceability sheet."""

    project_name: str
    rows: list[TraceRow] = field(default_factory=list)
