"""Structural types for the summary-by-group sheet."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["GroupSummary"]


@dataclass(frozen=True)
class GroupSummary:
    """Summary data for one guideline group."""

    group: str
    count: int
    names: str  # comma-separated guideline names
