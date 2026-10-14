"""FileInfo — metadata about a single file in a project data directory."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["FileInfo"]


@dataclass(frozen=True)
class FileInfo:
    """Metadata for a file inside a project's data directory.

    ``path`` is relative to the project root
    (e.g. ``data/requirements/01-brd.tsv``).
    """

    path: str
    name: str
    kind: str          # "yaml" | "tsv" | "puml" | "text"
    directory: str     # parent dir relative to project root, e.g. "data/requirements"
