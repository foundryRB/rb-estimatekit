"""Design markers precede Build markers; Build precedes Test in Lifecycle view."""

from __future__ import annotations

import pytest

from auditor.checks.roadmap.conftest import (
    check_lifecycle_build_before_test,
    check_lifecycle_design_before_build,
)
from auditor.tsv import read_tsv


def test_lifecycle_design_before_build(phase_files):
    """Design before Build in per-phase Lifecycle."""
    path = phase_files["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_lifecycle_design_before_build(path, read_tsv(path))


def test_lifecycle_build_before_test(phase_files):
    """Build before Test in per-phase Lifecycle."""
    path = phase_files["lifecycle"]
    if not path.exists():
        pytest.skip(f"{path.name} not found")
    check_lifecycle_build_before_test(path, read_tsv(path))
