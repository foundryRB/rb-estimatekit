"""Tests for Project aggregate root."""

from __future__ import annotations

from engine.domain.model.aggregates.project import Project
from engine.domain.model.entities.guideline import Guideline


class TestProjectCategories:
    """Project.discover_categories() behavior."""

    def test_discovers_unique_categories(self, minimal_project: Project) -> None:
        categories = minimal_project.discover_categories()
        names = [c.name for c in categories]
        assert names == ["Authentication", "Integration"]

    def test_empty_project_has_no_categories(self, config) -> None:
        project = Project(config=config)
        assert project.discover_categories() == []


class TestProjectEffort:
    """Project.compute_all_efforts() behavior."""

    def test_returns_effort_per_phase(self, minimal_project: Project) -> None:
        efforts = minimal_project.compute_all_efforts()
        assert "P1" in efforts
        assert efforts["P1"].build_total == 23.0


class TestProjectGuidelines:
    """Project.guidelines_for() behavior: the platform's rows and the phase's own."""

    def test_all_rows_govern_every_phase(self, minimal_project: Project) -> None:
        minimal_project.guidelines = [Guideline("G-1", "Positioning", "Channel", "Always")]
        assert [g.guideline_id for g in minimal_project.guidelines_for("P1")] == ["G-1"]
        assert [g.guideline_id for g in minimal_project.guidelines_for("P9")] == ["G-1"]

    def test_a_phases_rows_govern_only_that_phase(self, minimal_project: Project) -> None:
        minimal_project.guidelines = [
            Guideline("G-1", "Positioning", "Channel", "Always"),
            Guideline("G-2", "Integration", "Adapters", "P2", phase_ids=frozenset({"P2"})),
            Guideline("G-3", "Data", "Both", "P1 and P2", phase_ids=frozenset({"P1", "P2"})),
        ]
        assert [g.guideline_id for g in minimal_project.guidelines_for("P1")] == ["G-1", "G-3"]
        assert [g.guideline_id for g in minimal_project.guidelines_for("P2")] == [
            "G-1", "G-2", "G-3",
        ]

    def test_all_is_matched_regardless_of_case(self) -> None:
        guideline = Guideline("G-1", "Positioning", "Channel", "Always", frozenset({"all"}))
        assert guideline.applies_to("P7")


class TestProjectRequirementCounts:
    """Project.count_requirements_per_phase() behavior."""

    def test_counts_allocated_requirements(self, minimal_project: Project) -> None:
        counts = minimal_project.count_requirements_per_phase()
        assert counts["P1"] == 3  # All 3 requirements allocated to P1
