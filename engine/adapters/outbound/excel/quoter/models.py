"""Structural types for the quoter workbook."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuoterResourceRow:
    """A single resource row for the quoter sheet."""

    stream: str
    profile: str
    rate: float
    days: list[float]


@dataclass
class QuoterPhaseData:
    """Pre-computed quoter data for one phase."""

    phase_name: str
    phase_id: str
    project_name: str
    month_count: int
    plan: list[tuple[str, QuoterResourceRow | None]]  # ("data"|"sep", row_or_None)
