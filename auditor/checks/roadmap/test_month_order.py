"""Month columns are in correct phase/month order in All-phases files."""

from __future__ import annotations

from pathlib import Path

import pytest

from auditor.checks.roadmap.conftest import (
    check_all_phases_month_order,
    get_all_files,
)
from auditor.tsv import read_tsv


def test_all_resource_month_order(project_root: Path):
    """Month columns in correct order in Roadmap-ResourceAll.tsv."""
    path = get_all_files(project_root)["resource"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_all_phases_month_order(path, read_tsv(path), project_root, view="resource")


def test_all_activity_group_month_order(project_root: Path):
    """Month order in Roadmap-ActivityGroupAll.tsv."""
    path = get_all_files(project_root)["activity_group"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_all_phases_month_order(
        path, read_tsv(path), project_root, view="activity_group",
    )


def test_all_build_month_order(project_root: Path):
    """Month columns in correct order in Roadmap-BuildAll.tsv."""
    path = get_all_files(project_root)["build"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_all_phases_month_order(path, read_tsv(path), project_root, view="build")


def test_all_lifecycle_month_order(project_root: Path):
    """Month order in Roadmap-LifecycleAll.tsv."""
    path = get_all_files(project_root)["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_all_phases_month_order(path, read_tsv(path), project_root, view="lifecycle")
