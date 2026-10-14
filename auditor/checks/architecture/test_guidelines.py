"""Guidelines name the phases they govern, and every phase is governed by some.

A guideline row's ``Phase IDs`` is ``All`` (a principle of the platform) or the
ids of the phases whose decision it records; a deck renders the rows governing
the phase it sells. A row naming an undefined phase governs nothing, and a
phase no row governs would sell with an empty "governing decisions" slide.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from auditor.phases import discover_phases
from auditor.project import get_data_file
from auditor.tsv import read_tsv, read_tsv_raw

logger = logging.getLogger(__name__)

_ALL = "all"


def _guidelines_path(project_root: Path) -> Path:
    path = get_data_file(project_root, "architecture", "00-guidelines.tsv")
    if not path.exists():
        pytest.skip("No architecture guidelines file in this project")
    return path


def _governed_phases(row: dict[str, str]) -> set[str]:
    """The phase ids a guideline row governs; an empty cell governs all.

    Read as the engine reads the cell: ids separated by ``,`` or ``;``.
    """
    raw = (row.get("Phase IDs") or "").replace(";", ",")
    return {t.strip() for t in raw.split(",") if t.strip()} or {"All"}


def test_guidelines_declare_phase_ids(project_root: Path) -> None:
    """The guidelines file carries the Phase IDs column, spelled exactly.

    The engine reads an absent column as 'every row governs every phase', so a
    missing or misspelled header would make every phase's deck show every
    guideline while the per-phase checks below still pass.
    """
    path = _guidelines_path(project_root)
    rows = read_tsv_raw(path)
    assert rows, f"{path.name} is empty: give it a header row with the 'Phase IDs' column"
    header = rows[0]
    assert "Phase IDs" in header, (
        f"{path.name} has no 'Phase IDs' column (found: {', '.join(header)}); add it, "
        "with 'All' on every principle of the platform and the phase ids on a phase's "
        "own decisions"
    )


def test_guidelines_reference_defined_phases(project_root: Path) -> None:
    """Every Phase IDs value is 'All' or a phase defined in 02-phases.tsv."""
    path = _guidelines_path(project_root)
    defined = {p["phase_id"] for p in discover_phases(project_root)}

    invalid = [
        (row.get("Guideline ID", "").strip(), pid)
        for row in read_tsv(path)
        for pid in sorted(_governed_phases(row))
        if pid.lower() != _ALL and pid not in defined
    ]

    logger.info("Checked guideline phase references against %s", sorted(defined))
    assert not invalid, (
        f"{len(invalid)} guideline(s) name a phase the project does not define:\n"
        + "\n".join(f"  {gid} -> {pid}" for gid, pid in invalid[:10])
    )


def test_phase_has_governing_guidelines(phase: dict[str, Any], project_root: Path) -> None:
    """At least one guideline governs each defined phase ('All' or the phase's id)."""
    path = _guidelines_path(project_root)
    pid = phase["phase_id"]

    governing = [
        row
        for row in read_tsv(path)
        if any(p == pid or p.lower() == _ALL for p in _governed_phases(row))
    ]

    logger.info("%s: %d governing guideline(s)", pid, len(governing))
    assert governing, (
        f"{path.name} has no guideline governing phase {pid}: add rows whose "
        f"Phase IDs is 'All' or names {pid}"
    )
