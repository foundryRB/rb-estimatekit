"""Structural types for the guidelines overview sheet."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["GuidelineRow"]


@dataclass(frozen=True)
class GuidelineRow:
    """A single guideline row for the overview sheet."""

    group: str
    guideline_id: str
    name: str
    description: str
    phase_ids: str  # the phases it governs, comma-separated ("All" or phase ids)
