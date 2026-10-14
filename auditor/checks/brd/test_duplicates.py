"""No duplicate Req IDs in the BRD."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_no_duplicate_brd_requirements(project_root: Path) -> None:
    """No duplicate Req IDs in the BRD."""
    brd_path = get_data_file(project_root, "requirements", "01-brd.tsv")
    ids = [row.get("Req ID", "").strip() for row in read_tsv(brd_path)]
    duplicates = [rid for rid in ids if ids.count(rid) > 1]
    assert len(duplicates) == 0, f"Duplicates: {set(duplicates)}"
    logger.info("No duplicates among %d BRD requirements", len(ids))
