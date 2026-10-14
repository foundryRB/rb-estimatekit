"""No duplicate activity IDs within or across phases."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from auditor.activities import read_activities
from auditor.phases import discover_phases
from auditor.project import get_phase_file

logger = logging.getLogger(__name__)


@pytest.mark.project_integrity
def test_no_duplicate_activities(phase: dict[str, Any]) -> None:
    """No duplicate Activity IDs in the Build file."""
    build_path = get_phase_file(phase, "build_file")
    _, activities = read_activities(build_path)
    ids = [a["Activity ID"] for a in activities if a.get("Activity ID")]
    duplicates = [aid for aid in ids if ids.count(aid) > 1]
    assert len(duplicates) == 0, f"Duplicate Activity IDs: {set(duplicates)}"
    logger.info("No duplicates among %d activities", len(ids))


def test_no_activity_id_overlap_across_phases(project_root: Path) -> None:
    """Activity IDs do not overlap between phases."""
    phases = discover_phases(project_root)
    phase_ids_map: dict[str, set[str]] = {}

    for ph in phases:
        path = get_phase_file(ph, "build_file")
        if not path.exists():
            continue
        _, activities = read_activities(path)
        phase_ids_map[ph["phase_id"]] = {
            a["Activity ID"] for a in activities if a.get("Activity ID")
        }

    names = list(phase_ids_map.keys())
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            overlap = phase_ids_map[a] & phase_ids_map[b]
            assert len(overlap) == 0, (
                f"Activity IDs overlap between {a} and {b}: {overlap}"
            )
            logger.info(
                "No overlap: %s (%d) vs %s (%d)",
                a, len(phase_ids_map[a]), b, len(phase_ids_map[b]),
            )
