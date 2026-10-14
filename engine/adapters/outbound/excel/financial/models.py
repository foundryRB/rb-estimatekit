"""Structural types for the financial workbook."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["FinancialData"]


@dataclass(frozen=True)
class FinancialData:
    """Pre-computed data for a single financial workbook."""

    phase_name: str
    phase_id: str
    total_staff_days: float
