"""For each stream, resource capacity >= project effort."""

from __future__ import annotations

import logging
from typing import Any

from auditor.checks.activity.helpers import (
    parse_md,
    resource_grand_total,
    resource_total_by_stream,
)
from auditor.project import get_phase_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_stream_capacity(phase: dict[str, Any]) -> None:
    """For each stream, resource capacity >= project effort."""
    resource_path = get_phase_file(phase, "resource_file")
    project_path = get_phase_file(phase, "project_file")
    assert resource_path.exists() and project_path.exists()

    resource_rows = read_tsv(resource_path)
    project_rows = read_tsv(project_path)
    pid = phase["phase_id"]

    stream_effort: dict[str, float] = {}
    for row in project_rows:
        stream = row.get("Stream", "").strip()
        effort = parse_md(row.get("Effort (MD)", ""))
        if stream:
            stream_effort[stream] = stream_effort.get(stream, 0.0) + effort

    resource_total = resource_grand_total(resource_rows)
    project_total = sum(stream_effort.values())
    logger.info("%s Resource=%g MD, Project=%g MD", pid, resource_total, project_total)

    failures: list[str] = []
    for stream in sorted(stream_effort):
        effort = stream_effort[stream]
        capacity = resource_total_by_stream(resource_rows, stream)
        delta = capacity - effort
        status = "✔" if delta >= 0 else "⚠"
        logger.debug(
            "  %s %s: cap=%g, effort=%g, delta=%+g",
            status, stream, capacity, effort, delta,
        )
        if delta < 0:
            failures.append(f"{stream}: capacity ({capacity:g}) < effort ({effort:g})")

    assert not failures, f"{pid} stream deficits:\n  " + "\n  ".join(failures)
    assert resource_total >= project_total, (
        f"{pid} Resource ({resource_total:g}) < Project ({project_total:g})"
    )
