"""Output file naming conventions.

Constants and helpers for the Excel workbooks the system generates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.domain.model.value_objects.phase_id import PhaseId

OUT_REQUIREMENTS_XLSX = "Customer_Requirements_Matrix.xlsx"
OUT_ASSUMPTIONS_XLSX = "Assumptions_Register.xlsx"
OUT_GUIDELINES_XLSX = "Architecture_Guidelines.xlsx"


def out_estimation_xlsx(phase_id: PhaseId) -> str:
    return f"{phase_id}_Estimation.xlsx"


def out_quoter_xlsx(phase_id: PhaseId) -> str:
    return f"{phase_id}_Quoter.xlsx"


def out_financial_xlsx(phase_id: PhaseId) -> str:
    return f"{phase_id}_VROM.xlsx"
