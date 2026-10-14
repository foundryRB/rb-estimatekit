"""DiscoveredProject — a project found under the projects root, with its lifecycle state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__ = ["DiscoveredProject"]


@dataclass(frozen=True)
class DiscoveredProject:
    """A discovered project directory and whether it is archived."""

    path: Path
    archived: bool
