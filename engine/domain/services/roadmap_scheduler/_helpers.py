"""Pure helper functions shared across scheduling views."""

from __future__ import annotations

from engine.domain.model.value_objects.cell_marker import CellMarker


def month_labels(n: int) -> list[str]:
    """Generate month labels M1 … Mn."""
    return [f"M{i + 1}" for i in range(n)]


def first_true(flags: list[bool]) -> int | None:
    """Return index of the first True value, or None."""
    for i, f in enumerate(flags):
        if f:
            return i
    return None


def last_true(flags: list[bool]) -> int | None:
    """Return index of the last True value, or None."""
    for i in range(len(flags) - 1, -1, -1):
        if flags[i]:
            return i
    return None


def order_categories(active: dict[str, list], brd_order: list[str]) -> list[str]:
    """Order category keys following BRD priority, then remaining."""
    ordered: list[str] = []
    for c in brd_order:
        if c in active and c not in ordered:
            ordered.append(c)
    for c in active:
        if c not in ordered:
            ordered.append(c)
    return ordered


_MARKER_MAP = {
    "": CellMarker.EMPTY,
    "D": CellMarker.DESIGN,
    "·": CellMarker.ACTIVE,
    "◆": CellMarker.MILESTONE,
    "T": CellMarker.TEST_ACTIVE,
    "▲": CellMarker.TEST_MILESTONE,
}
