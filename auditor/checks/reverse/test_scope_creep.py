"""Reverse coverage: detect scope-creep by finding activities referencing
requirements not assigned to the current phase.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from auditor.activities import read_activity_req_map
from auditor.project import get_data_file, get_phase_file
from auditor.requirements import MATRIX_FIXED_COLUMNS, read_requirements_matrix
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def _read_all_requirements(matrix_path: Path) -> dict[str, dict[str, Any]]:
    """Return ``{req_id: {category, description, phases}}`` from the matrix."""
    reqs: dict[str, dict[str, Any]] = {}
    rows = read_tsv(matrix_path)
    if not rows:
        return reqs

    headers = list(rows[0].keys())
    for row in rows:
        req_id = row.get("Req ID", "").strip()
        if not req_id:
            continue
        phases_present = [
            h
            for h in headers
            if h not in MATRIX_FIXED_COLUMNS
            and row.get(h, "").strip()
        ]
        reqs[req_id] = {
            "category": row.get("Category", ""),
            "description": row.get("Description", ""),
            "phases": phases_present,
        }
    return reqs


@pytest.mark.project_integrity
def test_reverse_coverage(phase: dict[str, Any], project_root: Path) -> None:
    """Build activities only reference requirements assigned to this phase.

    A Req ID the matrix does not hold is assigned to no phase, so it is
    refused here as well. A whole-cell ``All`` is the phase's cross-cutting
    work and names no requirement.
    """
    matrix_path = get_data_file(project_root, "requirements", "03-matrix.tsv")
    build_path = get_phase_file(phase, "build_file")

    assert matrix_path.exists()
    assert build_path.exists(), f"Build file not found: {build_path}"

    phase_reqs = read_requirements_matrix(matrix_path, phase["phase_name"])
    phase_req_ids = set(phase_reqs.keys())

    all_reqs = _read_all_requirements(matrix_path)
    referenced, req_to_acts = read_activity_req_map(build_path)

    pid = phase["phase_id"]

    out_of_phase = sorted(
        rid for rid in referenced if rid not in phase_req_ids and rid in all_reqs
    )
    unknown = sorted(rid for rid in referenced if rid not in all_reqs)

    logger.info(
        "%s Reverse Coverage: %d refs, %d in-phase, %d out-of-phase, %d unknown",
        pid, len(referenced), len(phase_req_ids), len(out_of_phase), len(unknown),
    )

    if out_of_phase:
        for rid in out_of_phase:
            info = all_reqs[rid]
            acts = ", ".join(req_to_acts.get(rid, []))
            marked = ", ".join(info["phases"]) if info["phases"] else "NONE"
            logger.debug("  %s: %s", rid, info["description"])
            logger.debug("    Activities: %s, Marked in: %s", acts, marked)

    outside = [
        f"  {rid}: {all_reqs[rid]['description']} "
        f"[marked: {', '.join(all_reqs[rid]['phases'])}]"
        for rid in out_of_phase
    ] + [
        f"  {rid}: not in the requirements matrix "
        f"[in: {', '.join(req_to_acts.get(rid, []))}]"
        for rid in unknown
    ]
    assert len(outside) == 0, (
        f"{pid} Build references {len(outside)} out-of-phase requirement(s):\n"
        + "\n".join(outside)
    )
