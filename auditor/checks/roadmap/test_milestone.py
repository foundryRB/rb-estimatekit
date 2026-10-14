"""Milestone ◆ appears at end of active blocks in Build, Lifecycle, and Activity Group views."""

from __future__ import annotations

from pathlib import Path

import pytest

from auditor.checks.activity.helpers import read_config
from auditor.checks.roadmap.conftest import (
    check_activity_group_milestone_at_end,
    check_build_milestone_at_end,
    check_lifecycle_build_milestone_at_end,
    get_all_files,
)
from auditor.tsv import read_tsv


def test_build_milestone_at_end(phase_files):
    """Milestone ◆ at end of Build active block per-phase."""
    path = phase_files["build"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_build_milestone_at_end(path, read_tsv(path))


def test_lifecycle_build_milestone_at_end(phase_files):
    """Build milestone at end of build section in Lifecycle per-phase (▲ if testing integrated)."""
    path = phase_files["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    config = read_config(phase_files["config"])
    integrated = config["sit_days"] == 0 and config["uat_days"] == 0
    check_lifecycle_build_milestone_at_end(
        path, read_tsv(path), integrated_testing=integrated,
    )


def test_activity_group_milestone_at_end(phase_files):
    """Milestone ◆ at end of Activity Group block per-phase."""
    path = phase_files["activity_group"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_activity_group_milestone_at_end(path, read_tsv(path))


def test_all_build_milestone_at_end(project_root: Path):
    """Milestone at end in Roadmap-BuildAll.tsv."""
    path = get_all_files(project_root)["build"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_build_milestone_at_end(path, read_tsv(path))
