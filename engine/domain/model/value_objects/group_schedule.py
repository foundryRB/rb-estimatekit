"""GroupSchedule — intermediate scheduling result for activity groups."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["GroupSchedule"]


@dataclass(frozen=True)
class GroupSchedule:
    """Intermediate scheduling result for activity groups."""

    name: str
    stream: str
    effort: float
    start_month: int   # 0-based inclusive
    end_month: int     # 0-based inclusive (month containing milestone)
