"""Project root resolution and data file path helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

__all__ = [
    "get_data_file",
    "get_phase_file",
    "resolve_project_root",
    "try_resolve_project_root",
]


def resolve_project_root() -> Path:
    """Resolve the active project root.

    Priority:
      1. ``ESTIMATEKIT_PROJECT`` environment variable (absolute path).
      2. First subdirectory of ``projects/`` that contains ``project.yaml``.
    """
    env = os.environ.get("ESTIMATEKIT_PROJECT")
    if env:
        return Path(env).resolve()

    workspace = Path(__file__).resolve().parent.parent
    projects_dir = workspace / "projects"
    if projects_dir.is_dir():
        for child in sorted(projects_dir.iterdir()):
            if child.is_dir() and (child / "project.yaml").exists():
                return child

    msg = (
        "No project found. Set ESTIMATEKIT_PROJECT or place a project "
        "in projects/<slug>/ with a project.yaml."
    )
    raise RuntimeError(msg)


def try_resolve_project_root() -> tuple[Path | None, str | None]:
    """Resolve the project root without raising.

    Returns ``(root, None)`` on success and ``(None, problem)`` when no
    project can be found, so collection-time hooks can surface the problem
    as per-check outcomes instead of import errors.
    """
    try:
        return resolve_project_root(), None
    except RuntimeError as exc:
        return None, str(exc)


def get_data_file(project_root: Path, subdir: str, filename: str) -> Path:
    """Return the path to *filename* inside ``data/<subdir>/``.

    Example::

        get_data_file(root, "requirements", "01-brd.tsv")
        # → root / "data" / "requirements" / "01-brd.tsv"
    """
    return project_root / "data" / subdir / filename


def get_phase_file(phase: dict[str, Any], key: str) -> Path:
    """Return a resolved file path stored under *key* in a phase dict."""
    return phase[key]
