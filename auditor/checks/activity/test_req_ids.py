"""Every Build activity must have valid Req IDs: not empty, not N/A, well formed.

Valid values are:
  - Comma-separated requirement IDs (e.g. ``AUTH-001, SIM-002``)
  - ``All`` alone (any case): effort distributed across all BRD categories

Activities with ``N/A`` or blank Req IDs indicate data-entry gaps that break
the BRD-to-roadmap traceability chain. Any other cell shape is refused: the
roadmap misreads a ``;``, an empty entry, or ``All`` beside a Req ID, and ``All``
stands alone, so a repeated ``All`` is refused too.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from auditor.activities import read_activities
from auditor.project import get_phase_file
from auditor.requirements import req_ids_cell_problem

logger = logging.getLogger(__name__)


@pytest.mark.project_integrity
def test_build_activities_have_req_ids(phase: dict[str, Any]) -> None:
    """All Build activities must have non-empty, non-N/A, well-formed Req IDs."""
    build_path = get_phase_file(phase, "build_file")
    assert build_path.exists(), f"Build file not found: {build_path}"

    _, activities = read_activities(build_path)
    bad: list[str] = []
    for act in activities:
        act_id = act.get("Activity ID", "?")
        raw = act.get("Req IDs", "").strip()
        if not raw or raw.upper() == "N/A":
            bad.append(f"{act_id} (Req IDs={raw!r})")
        elif problem := req_ids_cell_problem(raw):
            bad.append(f"{act_id} (Req IDs={raw!r}) {problem}")

    pid = phase["phase_id"]
    logger.info("%s: %d activities checked, %d invalid", pid, len(activities), len(bad))
    assert not bad, (
        f"{pid} has {len(bad)} Build activities with missing, N/A, or malformed Req IDs:\n  "
        + "\n  ".join(bad)
        + "\nUse comma-separated Req IDs, or 'All' alone for foundational work."
    )
