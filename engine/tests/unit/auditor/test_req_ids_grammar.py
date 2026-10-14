"""Tests for the one grammar of a ``Req IDs`` cell, on the auditor's and the engine's side.

A cell is comma-separated Req IDs, or ``All`` alone (any case). The auditor
refuses every other shape, so the audit cannot pass a cell the engine misreads.
The engine splits on commas with no range expansion and reads ``All`` alone as
the cross-cutting sentinel; a repeated upper-case ``ALL`` collapses to that
sentinel, and the auditor refuses it because ``All`` stands alone.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from auditor.checks.activity import test_req_ids as activity_req_ids
from auditor.checks.architecture import test_guidelines as guidelines
from auditor.checks.assumptions import test_references as assumption_references
from auditor.phases import discover_phases
from auditor.requirements import req_ids_cell_problem
from engine.adapters.outbound.persistence.requirement_loaders import parse_req_ids_raw
from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.value_objects.requirement_id import RequirementId
from engine.domain.services.requirement_service import parse_req_ids
from engine.domain.services.roadmap_scheduler._build import compute_category_effort

WELL_FORMED = [
    "AUTH-001", "AUTH-001, DASH-001", "AUTH-001,DASH-001", "All", "all", "ALL", "N/A", "",
]
MISREAD = {
    "AUTH-001; DASH-001": "';'",
    "All;": "';'",
    "All,": "empty entry",
    "AUTH-001,": "empty entry",
    "AUTH-001,, DASH-001": "empty entry",
    "All, AUTH-001": "'All' stands alone",
}
"""Cells the auditor refuses and the roadmap misreads."""
REPEATED_ALL = {
    "All, All": "'All' stands alone",
    "all, all": "'All' stands alone",
    "ALL, ALL": "'All' stands alone",
    "ALL,ALL": "'All' stands alone",
}
"""Cells the auditor refuses because ``All`` stands alone."""
MALFORMED = {**MISREAD, **REPEATED_ALL}


def _phase(root: Path, phase_id: str = "P1") -> dict[str, Any]:
    return next(p for p in discover_phases(root) if p["phase_id"] == phase_id)


class TestGrammar:
    @pytest.mark.parametrize("cell", WELL_FORMED)
    def test_well_formed_cells_have_no_problem(self, cell: str) -> None:
        assert req_ids_cell_problem(cell) is None

    @pytest.mark.parametrize(("cell", "reason"), MALFORMED.items())
    def test_malformed_cells_name_their_problem(self, cell: str, reason: str) -> None:
        problem = req_ids_cell_problem(cell)
        assert problem is not None and reason in problem


class TestChecksRefuseMalformedCells:
    @pytest.mark.parametrize("cell", list(MALFORMED))
    def test_build_activity_check_fails(
        self, write_project: Callable[..., Path], cell: str,
    ) -> None:
        root = write_project(builds={"P1": ["AUTH-001", "DASH-001", cell]})
        with pytest.raises(AssertionError, match="malformed"):
            activity_req_ids.test_build_activities_have_req_ids(_phase(root))

    @pytest.mark.parametrize("cell", list(MALFORMED))
    def test_assumption_check_fails(
        self, write_project: Callable[..., Path], cell: str,
    ) -> None:
        root = write_project(assumptions=["All", cell])
        with pytest.raises(AssertionError, match="malformed"):
            assumption_references.test_assumption_req_ids_cells_are_well_formed(root)

    def test_well_formed_cells_pass_both_checks(self, write_project: Callable[..., Path]) -> None:
        root = write_project(
            builds={"P1": ["AUTH-001", "DASH-001", "All", "AUTH-001,DASH-001"]},
            assumptions=["All", "all", "AUTH-001, DASH-001"],
        )
        activity_req_ids.test_build_activities_have_req_ids(_phase(root))
        assumption_references.test_assumption_req_ids_cells_are_well_formed(root)


class TestEngineReadsTheGrammar:
    @pytest.mark.parametrize(
        ("cell", "ids"),
        [
            ("AUTH-001, DASH-001", {"AUTH-001", "DASH-001"}),
            ("All", {"ALL"}),
            ("all", {"ALL"}),
            ("N/A", set()),
            ("", set()),
            ("SIM-001-006", {"SIM-001-006"}),
        ],
    )
    def test_loader_reads_ids_and_expands_no_range(self, cell: str, ids: set[str]) -> None:
        assert parse_req_ids_raw(cell) == ids

    def test_domain_parser_reads_all_alone_as_the_sentinel(self) -> None:
        assert parse_req_ids("all") == {RequirementId("ALL")}
        assert parse_req_ids("AUTH-001, all") == {RequirementId("AUTH-001"), RequirementId("all")}


class TestEngineSpread:
    """A whole-cell ``All`` spreads across every category; misread shapes land under Unmatched."""

    @staticmethod
    def _effort(cell: str) -> dict[str, float]:
        activity = BuildActivity(
            activity_id="P1-BUILD-001", group="Core", name="Activity", effort_md=10,
            req_ids={RequirementId(r) for r in parse_req_ids_raw(cell)},
        )
        req_to_cat = {"BO-001": "Back Office", "AUTH-001": "Identity"}
        return dict(compute_category_effort([activity], req_to_cat, ["Back Office", "Identity"]))

    @pytest.mark.parametrize("cell", ["All", "all", "ALL"])
    def test_all_alone_spreads_across_every_category(self, cell: str) -> None:
        assert self._effort(cell) == {"Back Office": 5.0, "Identity": 5.0}

    @pytest.mark.parametrize("cell", list(MISREAD))
    def test_misread_shapes_land_under_unmatched(self, cell: str) -> None:
        assert self._effort(cell).get("Unmatched", 0.0) > 0

    @pytest.mark.parametrize("cell", ["ALL, ALL", "ALL,ALL"])
    def test_a_repeated_upper_all_is_refused_though_the_roadmap_spreads_it(
        self, cell: str,
    ) -> None:
        assert "stands alone" in (req_ids_cell_problem(cell) or "")
        assert self._effort(cell) == {"Back Office": 5.0, "Identity": 5.0}


class TestGuidelinePhaseIds:
    """The guideline checks read Phase IDs as the engine does: ',' or ';' separates ids."""

    @staticmethod
    def _project(tmp_path: Path, phase_ids: str) -> Path:
        req = tmp_path / "data" / "requirements"
        req.mkdir(parents=True)
        (req / "02-phases.tsv").write_text(
            "Phase\tPhase ID\nPhase 1\tP1\nPhase 2\tP2\n", encoding="utf-8",
        )
        arch = tmp_path / "data" / "architecture"
        arch.mkdir(parents=True)
        (arch / "00-guidelines.tsv").write_text(
            "Group\tGuideline ID\tGuideline\tDescription\tRationale\tPhase IDs\n"
            f"Data\tG-1\tOne\tDesc\tWhy\t{phase_ids}\n",
            encoding="utf-8",
        )
        return tmp_path

    @pytest.mark.parametrize("phase_ids", ["P1; P2", "P1,P2", "All;"])
    def test_both_separators_pass(self, tmp_path: Path, phase_ids: str) -> None:
        root = self._project(tmp_path, phase_ids)
        guidelines.test_guidelines_reference_defined_phases(root)
        for phase in discover_phases(root):
            guidelines.test_phase_has_governing_guidelines(phase, root)
