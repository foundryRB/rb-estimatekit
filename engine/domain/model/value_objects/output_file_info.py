"""OutputFileInfo — metadata about a generated output file."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["OutputFileInfo"]


@dataclass(frozen=True)
class OutputFileInfo:
    """Metadata for a generated output file.

    ``path`` is relative to the project root (e.g. ``output/excel/Roadmap.xlsx``).
    """

    name: str
    pipeline: str      # "roadmap" | "excel" | "slides"
    path: str          # relative path within project
    size: int          # file size in bytes
