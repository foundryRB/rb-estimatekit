"""A single resource cannot exceed the working-days ceiling in one month.

The capacity checks compare *aggregate* capacity against effort, so a month
cell booked above the ceiling only inflates capacity and never trips them. This
check guards the per-line, per-month ceiling directly: the scheduling model
fixes a month at ``DAYS_PER_MONTH`` working days, so one staffing line booked
above that is physically impossible — a hard data error, not an advisory smell.
"""

from __future__ import annotations

import logging
from typing import Any

from auditor.checks.activity.helpers import DAYS_PER_MONTH, overloaded_month_cells
from auditor.project import get_phase_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_resource_month_ceiling(phase: dict[str, Any]) -> None:
    """No resource line books more than DAYS_PER_MONTH man-days in a month."""
    resource_path = get_phase_file(phase, "resource_file")
    assert resource_path.exists(), f"Resource file not found: {resource_path}"

    rows = read_tsv(resource_path)
    pid = phase["phase_id"]
    offenders = overloaded_month_cells(rows)
    logger.info("%s ceiling: %d cell(s) over %d", pid, len(offenders), DAYS_PER_MONTH)

    failures = [
        f"{stream} / {profile} {month} = {value:g} MD (> {DAYS_PER_MONTH})"
        for stream, profile, month, value in offenders
    ]
    assert not failures, (
        f"{pid}: resource booked above {DAYS_PER_MONTH} working days in a month "
        f"(one line cannot exceed the month's capacity):\n  " + "\n  ".join(failures)
    )
