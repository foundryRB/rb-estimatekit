"""slides/ holds one executive summary and, optionally, one notes file per defined phase.

Every file under ``data/slides/`` is a phase's: ``<phase id>-executive-summary.tsv``
or ``<phase id>-notes.tsv`` for a phase the phase table defines. A file named
any other way belongs to no phase, so no deck reads it and nothing else in the
project tells the author it is dead content.
"""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.phases import discover_phases

logger = logging.getLogger(__name__)

_KINDS = ("executive-summary", "notes")


def test_slides_holds_only_phase_pitch_files(project_root: Path) -> None:
    """Every file under slides/ is a defined phase's executive summary or notes."""
    slides_dir = project_root / "data" / "slides"
    if not slides_dir.is_dir():
        return
    expected = {
        f"{phase['phase_id']}-{kind}.tsv"
        for phase in discover_phases(project_root)
        for kind in _KINDS
    }
    unknown = sorted(
        path.name for path in slides_dir.iterdir() if path.is_file() and path.name not in expected
    )

    logger.info("slides/: %d unknown file(s)", len(unknown))
    assert not unknown, (
        f"slides/ holds files that belong to no defined phase: {', '.join(unknown)}. "
        "Each file is <phase id>-executive-summary.tsv or <phase id>-notes.tsv; "
        "rename it to the phase it describes or delete it"
    )
