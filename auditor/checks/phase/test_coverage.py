"""Report requirements for each phase grouped by category."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_phase_requirements_identified(
    phase: dict[str, Any], project_root: Path,
) -> None:
    """Report requirements for a phase grouped by category (informational)."""
    matrix_path = get_data_file(project_root, "requirements", "03-matrix.tsv")
    phase_name = phase["phase_name"]
    pid = phase["phase_id"]

    reqs: list[dict[str, str]] = []
    for row in read_tsv(matrix_path):
        req_id = row.get("Req ID", "").strip()
        phase_val = row.get(phase_name, "").strip()
        if req_id and phase_val:
            reqs.append({
                "req_id": req_id,
                "category": row.get("Category", ""),
                "description": row.get("Description", ""),
                "phase_status": phase_val,
            })

    by_category: dict[str, list[dict[str, str]]] = {}
    for r in reqs:
        by_category.setdefault(r["category"], []).append(r)

    logger.info("%s (%s): %d requirements", pid, phase_name, len(reqs))
    for cat in sorted(by_category):
        logger.debug("  %s: %d", cat, len(by_category[cat]))
        for r in by_category[cat]:
            status = f"[{r['phase_status']}]" if r["phase_status"] != "✓" else ""
            logger.debug("    - %s: %s... %s", r["req_id"], r["description"][:50], status)
