"""Tests for the build activities' Req ID checks (activity coverage and reverse coverage).

A Req ID a build activity names must exist in the requirements matrix and be
assigned to the activity's phase. ``All`` as the whole cell is the cross-cutting
value and names no requirement; beside other IDs it is one more unknown ID.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from auditor.checks.activity import test_coverage as activity_coverage
from auditor.checks.reverse import test_scope_creep as reverse_coverage
from auditor.phases import discover_phases


def _phase(root: Path, phase_id: str = "P1") -> dict[str, Any]:
    """The discovered phase dict for *phase_id*."""
    return next(p for p in discover_phases(root) if p["phase_id"] == phase_id)


class TestUnknownReqIds:
    """An ID the matrix does not hold fails the activity check and the reverse check."""

    @pytest.mark.parametrize("bogus", ["NOPE-999", "AUTH-01"])
    def test_activity_check_fails_an_id_the_matrix_does_not_hold(
        self, write_project: Callable[..., Path], bogus: str,
    ) -> None:
        root = write_project(builds={"P1": ["AUTH-001", f"DASH-001, {bogus}"]})
        with pytest.raises(AssertionError, match=re.escape(bogus)):
            activity_coverage.test_activities_reference_valid_requirements(_phase(root), root)

    @pytest.mark.parametrize("bogus", ["NOPE-999", "AUTH-01"])
    def test_reverse_check_fails_an_id_the_matrix_does_not_hold(
        self, write_project: Callable[..., Path], bogus: str,
    ) -> None:
        root = write_project(builds={"P1": ["AUTH-001", f"DASH-001, {bogus}"]})
        with pytest.raises(AssertionError, match=re.escape(bogus)):
            reverse_coverage.test_reverse_coverage(_phase(root), root)

    def test_ids_the_phase_carries_pass_both_checks(
        self, write_project: Callable[..., Path],
    ) -> None:
        root = write_project()
        activity_coverage.test_activities_reference_valid_requirements(_phase(root), root)
        reverse_coverage.test_reverse_coverage(_phase(root), root)


class TestCrossCuttingAll:
    """``All`` alone in the cell passes; beside other IDs it is refused."""

    @pytest.mark.parametrize("cell", ["All", "ALL", "all"])
    def test_a_whole_cell_all_passes_both_checks(
        self, write_project: Callable[..., Path], cell: str,
    ) -> None:
        root = write_project(builds={"P1": ["AUTH-001", "DASH-001", cell]})
        activity_coverage.test_activities_reference_valid_requirements(_phase(root), root)
        reverse_coverage.test_reverse_coverage(_phase(root), root)

    def test_all_beside_other_ids_fails_the_activity_check(
        self, write_project: Callable[..., Path],
    ) -> None:
        root = write_project(builds={"P1": ["AUTH-001", "All, DASH-001"]})
        with pytest.raises(AssertionError, match="whole Req IDs cell"):
            activity_coverage.test_activities_reference_valid_requirements(_phase(root), root)

    def test_all_beside_other_ids_fails_the_reverse_check(
        self, write_project: Callable[..., Path],
    ) -> None:
        root = write_project(builds={"P1": ["AUTH-001", "All, DASH-001"]})
        with pytest.raises(AssertionError, match=r"\bAll\b"):
            reverse_coverage.test_reverse_coverage(_phase(root), root)
