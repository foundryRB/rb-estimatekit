"""PhaseConfig — per-phase scheduling parameters."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["PhaseConfig"]


@dataclass(frozen=True)
class PhaseConfig:
    """Per-phase scheduling parameters from Activities-{id}-Config.tsv."""

    design_lead_days: float = 0.0
    lag_pct: float = 0.0
    sit_days: float = 0.0
    uat_days: float = 0.0
