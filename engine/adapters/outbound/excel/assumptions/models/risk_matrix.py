"""Data shapes for the Risk Matrix sheet."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["CONF_ORDER", "IMPACT_ORDER", "KeyRisk", "RiskMatrixData"]

CONF_ORDER = ["HIGH", "MEDIUM", "LOW"]
IMPACT_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass(frozen=True)
class KeyRisk:
    """High-risk assumption summary for the Risk Matrix callout."""

    assumption_id: str
    short_title: str
    impact: str


@dataclass
class RiskMatrixData:
    """Pre-computed data for the Risk Matrix sheet."""

    project_name: str
    total: int
    matrix: dict[tuple[str, str], int] = field(default_factory=dict)
    key_risks: list[KeyRisk] = field(default_factory=list)
