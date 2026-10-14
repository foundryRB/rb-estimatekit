"""GroupEffort — effort summary for an activity group."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["GroupEffort"]


@dataclass(frozen=True)
class GroupEffort:
    """Effort summary for an activity group."""

    count: int          # Number of activities in group
    effort: float       # Total effort in man-days
