"""No duplicate Assumption IDs."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_no_duplicate_assumption_ids(project_root: Path) -> None:
    """No duplicate Assumption IDs."""
    path = get_data_file(project_root, "assumptions", "02-assumptions.tsv")
    ids = [row.get("Assumption ID", "").strip() for row in read_tsv(path)]
    duplicates = [aid for aid in ids if ids.count(aid) > 1]
    assert len(duplicates) == 0, f"Duplicates: {set(duplicates)}"
    logger.info("No duplicates among %d assumptions", len(ids))
