"""Tests for the cross-file consistency checks: BRD against matrix, matrix against phases."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from auditor.checks.consistency import test_brd_completeness as brd_completeness
from auditor.checks.consistency import test_phase_definitions as phase_definitions


class TestBrdAndMatrixHoldTheSameReqIds:
    """Each direction of a BRD/matrix disagreement fails."""

    def test_a_brd_requirement_missing_from_the_matrix_fails(
        self, write_project: Callable[..., Path],
    ) -> None:
        root = write_project(brd=["AUTH-001", "DASH-001", "SEC-001"])
        with pytest.raises(AssertionError, match="SEC-001"):
            brd_completeness.test_brd_completeness(root)

    def test_a_matrix_requirement_missing_from_the_brd_fails(
        self, write_project: Callable[..., Path],
    ) -> None:
        root = write_project(brd=["AUTH-001"])
        with pytest.raises(AssertionError, match="DASH-001"):
            brd_completeness.test_brd_completeness(root)

    def test_the_same_req_ids_pass(self, write_project: Callable[..., Path]) -> None:
        brd_completeness.test_brd_completeness(write_project())


class TestMatrixPhaseColumns:
    """The matrix's phase columns are exactly the phases the phase table defines."""

    @pytest.mark.parametrize("extra", ["Phase 2", "Priority"])
    def test_a_column_that_is_no_defined_phase_fails(
        self, write_project: Callable[..., Path], extra: str,
    ) -> None:
        root = write_project(matrix_columns=["Phase 1", extra])
        with pytest.raises(AssertionError, match=extra):
            phase_definitions.test_phase_definitions_match(root)

    def test_a_defined_phase_without_its_column_fails(
        self, write_project: Callable[..., Path],
    ) -> None:
        root = write_project(
            phases={"P1": "Phase 1", "P2": "Phase 2"}, matrix_columns=["Phase 1"],
        )
        with pytest.raises(AssertionError, match="Phase 2"):
            phase_definitions.test_phase_definitions_match(root)

    def test_columns_matching_the_defined_phases_pass(
        self, write_project: Callable[..., Path],
    ) -> None:
        root = write_project(phases={"P1": "Phase 1", "P2": "Phase 2"})
        phase_definitions.test_phase_definitions_match(root)
