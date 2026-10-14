"""ViewRow — a single row in a roadmap view."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.value_objects.cell_marker import CellMarker

__all__ = ["ViewRow"]


@dataclass(frozen=True)
class ViewRow:
    """A single row in a roadmap view (stream, group, or category)."""

    label: str
    effort: float
    cells: list[CellMarker] = field(default_factory=list)
    raw_values: list[float] | None = None  # numeric capacity (View 1 only)
    stream: str = ""  # work-stream label (View 2 only)
