"""Bundle: wraps all sheet data for the assumptions workbook."""

from __future__ import annotations

from dataclasses import dataclass

from .log import LogData
from .risk_matrix import RiskMatrixData
from .traceability import TraceabilityData

__all__ = ["AssumptionsData"]


@dataclass
class AssumptionsData:
    """All three sheets' data bundled together."""

    log: LogData
    risk_matrix: RiskMatrixData
    traceability: TraceabilityData
