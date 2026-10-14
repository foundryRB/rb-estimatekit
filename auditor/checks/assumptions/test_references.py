"""All Req IDs referenced in assumptions exist in the requirements matrix."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.project import get_data_file
from auditor.requirements import parse_req_ids, req_ids_cell_problem
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_assumptions_reference_valid_req_ids(project_root: Path) -> None:
    """All Req IDs referenced in assumptions exist in the requirements matrix.

    ``All`` (case-insensitive) stands for every requirement; the other IDs in
    its cell are still checked.
    """
    path = get_data_file(project_root, "assumptions", "02-assumptions.tsv")
    assert path.exists(), f"Assumptions not found: {path}"

    matrix = get_data_file(project_root, "requirements", "03-matrix.tsv")
    valid_reqs = {
        row.get("Req ID", "").strip()
        for row in read_tsv(matrix)
        if row.get("Req ID", "").strip()
    }
    assumptions = read_tsv(path)

    invalid_refs: list[tuple[str, str]] = []
    for assumption in assumptions:
        aid = assumption.get("Assumption ID", "").strip()
        referenced = parse_req_ids(assumption.get("Req IDs", ""))
        for req_id in sorted(referenced):
            if req_id.lower() != "all" and req_id not in valid_reqs:
                invalid_refs.append((aid, req_id))

    logger.info(
        "Checked %d assumptions against %d requirements",
        len(assumptions), len(valid_reqs),
    )
    assert len(invalid_refs) == 0, (
        f"{len(invalid_refs)} invalid Req ID references:\n"
        + "\n".join(f"  {aid} -> {rid}" for aid, rid in invalid_refs[:10])
    )


def test_assumption_req_ids_cells_are_well_formed(project_root: Path) -> None:
    """Every assumption's Req IDs cell is comma-separated Req IDs, or All alone."""
    path = get_data_file(project_root, "assumptions", "02-assumptions.tsv")
    assert path.exists(), f"Assumptions not found: {path}"

    bad: list[str] = []
    for assumption in read_tsv(path):
        raw = assumption.get("Req IDs", "").strip()
        problem = req_ids_cell_problem(raw)
        if problem:
            aid = assumption.get("Assumption ID", "?").strip()
            bad.append(f"{aid} (Req IDs={raw!r}) {problem}")

    assert not bad, (
        f"{len(bad)} malformed Req IDs cells:\n  " + "\n  ".join(bad[:10])
        + "\nUse comma-separated Req IDs, or 'All' alone for every requirement."
    )
