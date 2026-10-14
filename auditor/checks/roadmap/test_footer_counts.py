"""Footer row counts match actual marker counts in Build and Lifecycle views."""

from __future__ import annotations

from pathlib import Path

import pytest

from auditor.checks.roadmap.conftest import (
    check_build_footer_counts,
    check_lifecycle_footer_counts,
    check_resource_totals,
    get_all_files,
)
from auditor.tsv import read_tsv


def test_build_footer_counts(phase_files):
    """Footer counts match markers in per-phase Build."""
    path = phase_files["build"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_build_footer_counts(path, read_tsv(path))


def test_lifecycle_footer_counts(phase_files):
    """Footer counts match markers in per-phase Lifecycle."""
    path = phase_files["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_lifecycle_footer_counts(path, read_tsv(path))


def test_resource_totals(phase_files):
    """Resource TOTAL footer sums match column sums."""
    path = phase_files["resource"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_resource_totals(path, read_tsv(path))


def test_all_build_footer_counts(project_root: Path):
    """Footer counts in Roadmap-BuildAll.tsv."""
    path = get_all_files(project_root)["build"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_build_footer_counts(path, read_tsv(path))


def test_all_lifecycle_footer_counts(project_root: Path):
    """Footer counts in Roadmap-LifecycleAll.tsv."""
    path = get_all_files(project_root)["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_lifecycle_footer_counts(path, read_tsv(path))
