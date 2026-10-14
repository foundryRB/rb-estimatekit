"""All Effort (MD) values are numeric; Resource values are numeric."""

from __future__ import annotations

from pathlib import Path

import pytest

from auditor.checks.roadmap.conftest import (
    check_effort_numeric,
    check_resource_numeric,
    get_all_files,
)
from auditor.tsv import read_tsv


def test_build_effort_numeric(phase_files):
    """Effort (MD) values are numeric in per-phase Build."""
    path = phase_files["build"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_effort_numeric(path, read_tsv(path))


def test_lifecycle_effort_numeric(phase_files):
    """Effort (MD) values are numeric in per-phase Lifecycle."""
    path = phase_files["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_effort_numeric(path, read_tsv(path))


def test_resource_numeric(phase_files):
    """Resource values are numeric in per-phase Resource."""
    path = phase_files["resource"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_resource_numeric(path, read_tsv(path))


def test_all_build_effort_numeric(project_root: Path):
    """Effort numeric in Roadmap-BuildAll.tsv."""
    path = get_all_files(project_root)["build"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_effort_numeric(path, read_tsv(path))


def test_all_lifecycle_effort_numeric(project_root: Path):
    """Effort numeric in Roadmap-LifecycleAll.tsv."""
    path = get_all_files(project_root)["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_effort_numeric(path, read_tsv(path))
