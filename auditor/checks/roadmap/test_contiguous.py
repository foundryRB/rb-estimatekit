"""No gaps in marker blocks across all four roadmap views."""

from __future__ import annotations

import pytest

from auditor.checks.roadmap.conftest import (
    check_activity_group_contiguous,
    check_build_contiguous,
    check_lifecycle_contiguous,
)
from auditor.tsv import read_tsv


def test_build_contiguous(phase_files):
    """No gaps in per-phase Build marker blocks."""
    path = phase_files["build"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_build_contiguous(path, read_tsv(path))


def test_lifecycle_contiguous(phase_files):
    """No gaps in per-phase Lifecycle marker blocks."""
    path = phase_files["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_lifecycle_contiguous(path, read_tsv(path))


def test_activity_group_contiguous(phase_files):
    """No gaps in per-phase Activity Group marker blocks."""
    path = phase_files["activity_group"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_activity_group_contiguous(path, read_tsv(path))
