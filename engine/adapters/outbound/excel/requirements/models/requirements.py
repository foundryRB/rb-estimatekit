"""Structural types for the requirements-by-phase sheet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReqMatrixRow:
    """One requirement row for the matrix sheet."""

    req_id: str
    description: str
    phase_allocations: dict[str, str]  # phase_id → alloc display text
