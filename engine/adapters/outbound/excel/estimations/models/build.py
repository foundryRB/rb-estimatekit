"""Structural types for the build activities sheet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BuildActivityRow:
    """A single build activity row."""

    name: str
    req_ids_str: str
    effort_md: float
    group: str


@dataclass(frozen=True)
class BuildGroupData:
    """A group of build activities with subtotal."""

    group_name: str
    activities: list[BuildActivityRow]
    subtotal: float
