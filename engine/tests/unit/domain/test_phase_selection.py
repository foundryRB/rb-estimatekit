"""Tests for select_phase: the deck sells one phase, and the caller names it."""

from __future__ import annotations

import pytest

from engine.domain.exceptions import (
    PhaseInputMissingError,
    PhaseNotFoundError,
    PhaseRequiredError,
)
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.entities.executive_summary_data import ExecutiveSummaryData
from engine.domain.services.phase_selection import select_phase, select_phase_with_pitch


class TestSelectPhase:
    def test_a_single_phase_project_needs_no_name(self, minimal_project: Project) -> None:
        assert select_phase(minimal_project, None).phase_id == "P1"

    def test_a_named_phase_is_returned(self, minimal_project: Project) -> None:
        minimal_project.phases.append(Phase(phase_id="P2", name="Two", description=""))
        assert select_phase(minimal_project, "P2").phase_id == "P2"

    def test_a_multi_phase_project_refuses_an_unnamed_deck(
        self, minimal_project: Project
    ) -> None:
        minimal_project.phases.append(Phase(phase_id="P2", name="Two", description=""))
        with pytest.raises(PhaseRequiredError) as excinfo:
            select_phase(minimal_project, None)
        assert "P1, P2" in str(excinfo.value)

    def test_an_unknown_phase_is_refused_with_the_defined_ones(
        self, minimal_project: Project
    ) -> None:
        with pytest.raises(PhaseNotFoundError) as excinfo:
            select_phase(minimal_project, "P9")
        assert "P9" in str(excinfo.value)
        assert "P1" in str(excinfo.value)

    def test_a_project_without_phases_has_no_deck(self, config) -> None:
        with pytest.raises(PhaseRequiredError) as excinfo:
            select_phase(Project(config=config), None)
        assert "no phases" in str(excinfo.value)


class TestSelectPhaseWithPitch:
    def test_a_phase_without_its_executive_summary_is_refused_by_path(
        self, minimal_project: Project
    ) -> None:
        with pytest.raises(PhaseInputMissingError) as excinfo:
            select_phase_with_pitch(minimal_project, None)
        assert "data/slides/P1-executive-summary.tsv" in str(excinfo.value)

    def test_an_empty_executive_summary_counts_as_missing(
        self, minimal_project: Project
    ) -> None:
        minimal_project.phases[0].executive_summary = ExecutiveSummaryData()
        with pytest.raises(PhaseInputMissingError):
            select_phase_with_pitch(minimal_project, "P1")

    def test_a_phase_with_its_pitch_is_returned(self, minimal_project: Project) -> None:
        minimal_project.phases[0].executive_summary = ExecutiveSummaryData(
            context_description="Sells P1"
        )
        assert select_phase_with_pitch(minimal_project, None).phase_id == "P1"
