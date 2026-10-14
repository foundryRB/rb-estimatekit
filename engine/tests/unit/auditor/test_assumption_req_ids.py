"""Tests for the assumptions' Req ID check: ``All`` never hides the other IDs in its cell."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from auditor.checks.assumptions import test_references as assumption_references


class TestAssumptionReqIds:
    """Every Req ID an assumption names exists in the matrix; ``All`` stands for every one."""

    @pytest.mark.parametrize("cell", ["All, NOPE-1", "ALL; NOPE-1", "AUTH-001, NOPE-1"])
    def test_an_id_the_matrix_does_not_hold_fails(
        self, write_project: Callable[..., Path], cell: str,
    ) -> None:
        root = write_project(assumptions=["All", cell])
        with pytest.raises(AssertionError, match="NOPE-1"):
            assumption_references.test_assumptions_reference_valid_req_ids(root)

    @pytest.mark.parametrize("cell", ["All", "all", "All, AUTH-001", "AUTH-001, DASH-001"])
    def test_all_and_ids_the_matrix_holds_pass(
        self, write_project: Callable[..., Path], cell: str,
    ) -> None:
        root = write_project(assumptions=[cell])
        assumption_references.test_assumptions_reference_valid_req_ids(root)
