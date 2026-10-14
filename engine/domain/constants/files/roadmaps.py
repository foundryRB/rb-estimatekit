"""Roadmap file naming conventions.

Helpers for building roadmap output filenames.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.domain.model.value_objects.phase_id import PhaseId


def roadmap_file(view: str, phase_id: PhaseId) -> str:
    """Build a roadmap output filename.

    >>> roadmap_file("Resource", "P1")
    'Roadmap-ResourceP1.tsv'
    """
    return f"Roadmap-{view}{phase_id}.tsv"
