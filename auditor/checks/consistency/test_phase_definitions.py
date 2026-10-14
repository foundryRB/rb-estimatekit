"""Phase columns in the matrix align with Phases TSV definitions."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.phases import discover_phases
from auditor.project import get_data_file
from auditor.requirements import MATRIX_FIXED_COLUMNS
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_phase_definitions_match(project_root: Path) -> None:
    """Phase columns in the requirements matrix align with Phases TSV.

    Every defined phase has its matrix column, and every matrix column apart
    from Category, Req ID, Description and Notes is a defined phase.
    """
    matrix_path = get_data_file(project_root, "requirements", "03-matrix.tsv")
    phases = discover_phases(project_root)

    matrix_rows = read_tsv(matrix_path)
    phase_names = [p["phase_name"] for p in phases]

    logger.info("Defined phases: %s", phase_names)

    phase_counts: dict[str, int] = {}
    for pname in phase_names:
        count = sum(1 for row in matrix_rows if row.get(pname, "").strip())
        phase_counts[pname] = count
        logger.debug("  %s: %d requirements", pname, count)

    matrix_header = list(matrix_rows[0].keys()) if matrix_rows else []
    for pname in phase_names:
        assert pname in matrix_header, (
            f"Phase '{pname}' defined in Phases TSV but not a column "
            "in RequirementsMatrix"
        )

    undefined = [
        h for h in matrix_header
        if h and h not in MATRIX_FIXED_COLUMNS and h not in phase_names
    ]
    assert len(undefined) == 0, (
        f"RequirementsMatrix has {len(undefined)} column(s) that name no phase defined "
        f"in Phases TSV: {', '.join(undefined)} (besides Category, Req ID, Description "
        "and Notes, the matrix holds one column per defined phase: delete any other "
        "column, such as a dropped phase's, or define the phase)"
    )
