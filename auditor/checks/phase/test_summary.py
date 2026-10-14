"""Summary of requirements across all phases; identifies multi-phase items."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.phases import discover_phases
from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_all_phases_summary(project_root: Path) -> None:
    """Summary of requirements across all phases."""
    phases = discover_phases(project_root)
    matrix_path = get_data_file(project_root, "requirements", "03-matrix.tsv")
    matrix_rows = read_tsv(matrix_path)

    phase_ids_map: dict[str, set[str]] = {}
    for ph in phases:
        ids: set[str] = set()
        for row in matrix_rows:
            req_id = row.get("Req ID", "").strip()
            if req_id and row.get(ph["phase_name"], "").strip():
                ids.add(req_id)
        phase_ids_map[ph["phase_id"]] = ids
        logger.info(
            "%s (%s): %d requirements", ph["phase_id"], ph["phase_name"], len(ids),
        )

    all_ids: set[str] = set()
    for ids in phase_ids_map.values():
        all_ids |= ids
    logger.info("Total unique: %d", len(all_ids))

    multi: list[tuple[str, list[str]]] = []
    for req_id in all_ids:
        in_phases = [pid for pid, ids in phase_ids_map.items() if req_id in ids]
        if len(in_phases) > 1:
            multi.append((req_id, in_phases))

    if multi:
        logger.info("Multi-phase requirements (%d):", len(multi))
        for req_id, phase_list in sorted(multi):
            logger.debug("  %s: %s", req_id, ", ".join(phase_list))
