"""Structural types for the category summary sheet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategorySummaryRow:
    """One category row for the category summary sheet."""

    display_name: str
    total: int
    phase_counts: dict[str, int]  # phase_id → count
