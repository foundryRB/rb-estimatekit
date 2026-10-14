"""The BRD and the requirements matrix hold the same Req IDs."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_brd_completeness(project_root: Path) -> None:
    """Every Req ID in the matrix exists in the BRD, and every BRD Req ID has its matrix row.

    A BRD requirement missing from the matrix is assigned to no phase.
    """
    matrix_path = get_data_file(project_root, "requirements", "03-matrix.tsv")
    brd_path = get_data_file(project_root, "requirements", "01-brd.tsv")

    brd_reqs = {
        row.get("Req ID", "").strip()
        for row in read_tsv(brd_path)
        if row.get("Req ID", "").strip()
    }
    matrix_reqs = {
        row.get("Req ID", "").strip()
        for row in read_tsv(matrix_path)
        if row.get("Req ID", "").strip()
    }

    missing = matrix_reqs - brd_reqs
    orphaned = brd_reqs - matrix_reqs

    logger.info("Matrix: %d, BRD: %d", len(matrix_reqs), len(brd_reqs))

    disagreements = [
        f"  {r}: in the matrix, missing from the BRD" for r in sorted(missing)
    ] + [
        f"  {r}: in the BRD, missing from the matrix (assigned to no phase)"
        for r in sorted(orphaned)
    ]
    assert len(disagreements) == 0, (
        f"BRD and matrix disagree on {len(disagreements)} Req ID(s):\n"
        + "\n".join(disagreements)
    )
