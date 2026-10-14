"""All phase requirements from the matrix are covered in Build activities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from auditor.activities import read_activities, read_activity_req_map
from auditor.project import get_data_file, get_phase_file
from auditor.requirements import read_requirements_matrix
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_requirements_coverage(phase: dict[str, Any], project_root: Path) -> None:
    """Every requirement assigned to this phase has at least one Build activity."""
    matrix_path = get_data_file(project_root, "requirements", "03-matrix.tsv")
    build_path = get_phase_file(phase, "build_file")

    assert matrix_path.exists(), f"Requirements matrix not found: {matrix_path}"
    assert build_path.exists(), f"Build file not found: {build_path}"

    requirements = read_requirements_matrix(matrix_path, phase["phase_name"])
    referenced, activities = read_activities(build_path)

    pid = phase["phase_id"]
    logger.info(
        "%s Requirements Coverage: %d reqs, %d refs, %d activities",
        pid, len(requirements), len(referenced), len(activities),
    )

    uncovered = [(rid, info) for rid, info in requirements.items() if rid not in referenced]
    covered = len(requirements) - len(uncovered)
    pct = (covered / len(requirements) * 100) if requirements else 0
    logger.info("Coverage: %.1f%% (%d/%d)", pct, covered, len(requirements))

    if uncovered:
        for rid, info in sorted(uncovered):
            logger.debug("  UNCOVERED: %s: %s", rid, info["description"])

    assert len(uncovered) == 0, (
        f"{pid} Build activities do not cover {len(uncovered)} requirements:\n"
        + "\n".join(
            f"  {rid}: {info['description']}" for rid, info in sorted(uncovered)
        )
    )


@pytest.mark.project_integrity
def test_activities_reference_valid_requirements(
    phase: dict[str, Any], project_root: Path,
) -> None:
    """All requirement IDs referenced in activities exist in the matrix.

    A whole-cell ``All`` marks a cross-cutting activity and names no ID; an
    ``All`` beside other IDs is checked as one more ID, and refused.
    """
    matrix_path = get_data_file(project_root, "requirements", "03-matrix.tsv")
    build_path = get_phase_file(phase, "build_file")

    all_requirements = {
        row.get("Req ID", "").strip()
        for row in read_tsv(matrix_path)
        if row.get("Req ID", "").strip()
    }

    referenced, req_to_acts = read_activity_req_map(build_path)
    invalid = sorted(r for r in referenced if r not in all_requirements)

    pid = phase["phase_id"]
    logger.info(
        "%s: %d referenced requirements checked against matrix (%d total), %d unknown",
        pid, len(referenced), len(all_requirements), len(invalid),
    )

    hint = (
        "\n'All' marks a cross-cutting activity only as the whole Req IDs cell."
        if any(r.lower() == "all" for r in invalid)
        else ""
    )
    assert len(invalid) == 0, (
        f"{pid} Build activities reference {len(invalid)} Req ID(s) "
        "the requirements matrix does not hold:\n"
        + "\n".join(f"  {rid} (in {', '.join(req_to_acts[rid])})" for rid in invalid)
        + hint
    )
