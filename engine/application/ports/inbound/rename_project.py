"""Inbound port: rename a project's display name and/or slug."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["RenameProjectPort"]


@runtime_checkable
class RenameProjectPort(Protocol):
    """Rename a project: its display name, its slug, or both."""

    def execute(
        self,
        projects_root: Path,
        slug: str,
        *,
        new_slug: str | None = None,
        new_name: str | None = None,
    ) -> Path:
        """Rename the project at *projects_root/slug*.

        A slug rename moves the project directory atomically; a malformed
        or occupied target slug is refused. Returns the project's path
        after the rename.
        """
        ...
