"""Data preparation for the Financial Model workbook."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import FinancialData

if TYPE_CHECKING:
    from engine.domain.model.aggregates.phase import Phase

__all__ = ["prepare_financial"]


def prepare_financial(phase: Phase) -> FinancialData | None:
    """Extract placeholder values from a phase. Returns None if no capacity."""
    total_sd = phase.resource_plan.total_capacity
    if total_sd == 0:
        return None
    return FinancialData(
        phase_name=phase.name,
        phase_id=phase.phase_id,
        total_staff_days=total_sd,
    )
