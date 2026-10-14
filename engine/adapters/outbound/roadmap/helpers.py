"""Shared helpers for roadmap TSV generation."""

from __future__ import annotations

__all__ = ["last_true", "order_cats"]


def order_cats(raw: dict, view_rows: list) -> list[str]:
    """Get ordered category list from view rows, falling back to raw keys."""
    if view_rows:
        return [r.label for r in view_rows]
    return list(raw.keys())


def last_true(flags: list[bool]) -> int | None:
    """Return the index of the last True value in *flags*, or None."""
    for i in range(len(flags) - 1, -1, -1):
        if flags[i]:
            return i
    return None
