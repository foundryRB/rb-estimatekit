"""Structural types for the project estimate sheet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EstimateRow:
    """A row in the project estimate sheet."""

    label: str
    effort_md: float
    is_header: bool = False
