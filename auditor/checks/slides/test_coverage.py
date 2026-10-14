"""Every defined phase has the executive summary its deck renders.

The deck sells one phase, and its executive summary is that phase's pitch,
read from ``slides/P<n>-executive-summary.tsv``. A phase without one has no
pitch to sell; a phase whose file carries no context description has an empty
one. Speaker notes (``P<n>-notes.tsv``) are optional: a deck renders without them.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auditor.helpers import fail_if_file_missing
from auditor.project import get_phase_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_phase_executive_summary_defined(phase: dict[str, Any], project_root: Path) -> None:
    """Each defined phase has an executive summary with a context description."""
    pid = phase["phase_id"]
    path = get_phase_file(phase, "executive_summary_file")
    fail_if_file_missing(path, f"Executive summary for phase {pid}")

    rows = read_tsv(path)
    described = [
        row
        for row in rows
        if row.get("Section", "").strip() == "Context"
        and row.get("Key", "").strip() == "Description"
        and row.get("Value", "").strip()
    ]
    logger.info(
        "%s: %d executive-summary row(s), %d description(s)", pid, len(rows), len(described),
    )
    assert described, (
        f"{path.name} has no 'Context / Description' row with a value: "
        f"phase {pid} has no pitch for its deck to sell"
    )
