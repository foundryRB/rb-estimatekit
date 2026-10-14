"""CLI-layer representation of a project summary."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SummaryView:
    """Plain CLI-layer representation of a project summary."""

    name: str
    client: str
    description: str
    phase_count: int
    requirement_count: int
    assumption_count: int
    phases: list[str] = field(default_factory=list)
