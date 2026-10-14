"""Structural types for the summary sheet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseOverviewRow:
    """One phase row for the summary sheet."""

    name: str
    req_label: str  # e.g. "5/12 (42%)"
    description: str


@dataclass(frozen=True)
class EffortRow:
    """One phase effort row for the investment summary."""

    name: str
    build: float
    overhead: float
    total: float
