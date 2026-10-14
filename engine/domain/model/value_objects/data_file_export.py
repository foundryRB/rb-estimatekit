"""DataFileExport — a data file's relative path and raw content for archival."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["DataFileExport"]


@dataclass(frozen=True)
class DataFileExport:
    """A data file entry ready for export.

    ``path`` is relative to the project root
    (e.g. ``data/requirements/01-brd.tsv``).
    ``content`` is the raw file bytes.
    """

    path: str
    content: bytes
