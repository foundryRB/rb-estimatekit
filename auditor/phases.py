"""Phase discovery from project data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from auditor.project import get_data_file, try_resolve_project_root
from auditor.tsv import read_tsv

__all__ = [
    "discover_phases",
    "missing_phases_file",
    "phase_discovery_problem",
    "phases_file",
]


def phases_file(project_root: Path) -> Path:
    """Path to the phase-definitions file, ``data/requirements/02-phases.tsv``."""
    return get_data_file(project_root, "requirements", "02-phases.tsv")


def missing_phases_file(project_root: Path) -> str | None:
    """Message naming the phase-definitions file when absent, else ``None``."""
    path = phases_file(project_root)
    if path.exists():
        return None
    return f"Required data file missing: {path}"


def phase_discovery_problem() -> str | None:
    """Why phase discovery cannot run: no project, or no phase-definitions file.

    Returns ``None`` when discovery can proceed. Collection-time hooks call
    this before ``discover_phases`` so missing inputs surface as per-check
    outcomes, never as collection errors.
    """
    project_root, problem = try_resolve_project_root()
    if problem or project_root is None:
        return problem or "No project found."
    return missing_phases_file(project_root)


def discover_phases(project_root: Path) -> list[dict[str, Any]]:
    """Discover phases from ``requirements/02-phases.tsv``.

    Returns a list of dicts, each containing:
      - ``phase_id``               - e.g. ``"P1"``
      - ``phase_name``             - e.g. ``"Phase 1"``
      - ``build_file``             - ``Path`` to ``activities/<id>-build.tsv``
      - ``project_file``           - ``Path`` to ``activities/<id>-project.tsv``
      - ``resource_file``          - ``Path`` to ``activities/<id>-resource.tsv``
      - ``config_file``            - ``Path`` to ``activities/<id>-config.tsv``
      - ``executive_summary_file`` - ``Path`` to ``slides/<id>-executive-summary.tsv``
      - ``notes_file``             - ``Path`` to ``slides/<id>-notes.tsv``
    """
    rows = read_tsv(phases_file(project_root))
    act_dir = project_root / "data" / "activities"
    slides_dir = project_root / "data" / "slides"

    phases: list[dict[str, Any]] = []
    for row in rows:
        phase_id = row.get("Phase ID", "").strip()
        phase_name = row.get("Phase", "").strip()
        if not phase_id:
            continue
        phases.append({
            "phase_id": phase_id,
            "phase_name": phase_name,
            "build_file": act_dir / f"{phase_id}-build.tsv",
            "project_file": act_dir / f"{phase_id}-project.tsv",
            "resource_file": act_dir / f"{phase_id}-resource.tsv",
            "config_file": act_dir / f"{phase_id}-config.tsv",
            "executive_summary_file": slides_dir / f"{phase_id}-executive-summary.tsv",
            "notes_file": slides_dir / f"{phase_id}-notes.tsv",
        })
    return phases
