"""Project-level Build effort matches sum of Build activities.

Convention:
  The Build TSV details work from the Design stream plus the ``Build
  Activities`` group.  The only hardcoded name is ``Build Activities`` —
  everything else is resolved via the ``Stream`` column.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from auditor.activities import read_activities
from auditor.project import get_phase_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def _is_build_detailed(row: dict[str, str]) -> bool:
    """Return True if a Project activity group is detailed in the Build TSV.

    A group qualifies when it is *either*:
      - the documented ``Build Activities`` convention, or
      - assigned to a Design stream (stream name contains ``'Design'``).
    """
    group = row.get("Activity Group", "").strip()
    stream = row.get("Stream", "").strip()
    if group == "Build Activities":
        return True
    return "Design" in stream


def test_project_totals_consistency(phase: dict[str, Any]) -> None:
    """Build TSV total equals sum of build-detailed Project groups."""
    build_path = get_phase_file(phase, "build_file")
    project_path = get_phase_file(phase, "project_file")

    assert build_path.exists(), f"Build file not found: {build_path}"
    assert project_path.exists(), f"Project file not found: {project_path}"

    _, activities = read_activities(build_path)
    build_total = 0.0
    for act in activities:
        effort_str = act.get("Effort (MD)", "").strip()
        if effort_str:
            with contextlib.suppress(ValueError):
                build_total += float(effort_str)

    project_build = 0.0
    matched_groups: list[str] = []
    for row in read_tsv(project_path):
        if _is_build_detailed(row):
            group = row.get("Activity Group", "").strip()
            effort_str = row.get("Effort (MD)", "").strip()
            if effort_str:
                try:
                    project_build += float(effort_str)
                    matched_groups.append(f"{group}={effort_str}")
                except ValueError:
                    pass

    pid = phase["phase_id"]
    logger.info(
        "%s Build total: activities=%g MD, project=%g MD (%s)",
        pid, build_total, project_build, " + ".join(matched_groups),
    )
    assert abs(build_total - project_build) < 1e-6, (
        f"{pid} effort mismatch: Build TSV={build_total:g} MD vs "
        f"Project({' + '.join(matched_groups)})={project_build:g} MD"
    )
