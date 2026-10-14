"""Category — functional category grouping related requirements."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Category"]


@dataclass(frozen=True)
class Category:
    """Functional category grouping related requirements."""

    name: str                       # "Authentication & Access Control"
    short_name: str | None = None   # "Authentication" (from BRD, optional)

    @property
    def display_name(self) -> str:
        """Return short_name if available, otherwise full name."""
        return self.short_name or self.name
