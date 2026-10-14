"""Tests for Phase aggregate — effort computation and scheduling."""

from __future__ import annotations

from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.entities.project_activity import ProjectActivity
from engine.domain.model.entities.slide_note import SlideNote


class TestPhaseSlideNotes:
    """Phase.get_slide_note() behavior: the pitch copy is the phase's own."""

    def test_returns_none_when_no_notes(self, minimal_phase: Phase) -> None:
        assert minimal_phase.get_slide_note("effort", "footer-note") is None

    def test_returns_the_note_for_the_slot(self, minimal_phase: Phase) -> None:
        minimal_phase.slide_notes.append(SlideNote("effort", "footer-note", "Stable team"))
        assert minimal_phase.get_slide_note("effort", "footer-note") == "Stable team"
        assert minimal_phase.get_slide_note("effort", "speaker") is None


class TestPhaseEffort:
    """Phase.compute_effort() behavior."""

    def test_empty_phase_has_zero_effort(self) -> None:
        phase = Phase(phase_id="P1", name="Empty", description="")
        effort = phase.compute_effort()
        assert effort.build_total == 0.0
        assert effort.overhead_total == 0.0
        assert effort.authored_total == 0.0
        assert effort.staffed_capacity == 0.0

    def test_groups_build_activities(self, minimal_phase: Phase) -> None:
        effort = minimal_phase.compute_effort()
        assert "Core" in effort.build_groups
        assert "Integration" in effort.build_groups
        assert effort.build_groups["Core"].count == 2
        assert effort.build_groups["Core"].effort == 15.0
        assert effort.build_groups["Integration"].count == 1
        assert effort.build_groups["Integration"].effort == 8.0

    def test_build_total_is_sum_of_groups(self, minimal_phase: Phase) -> None:
        effort = minimal_phase.compute_effort()
        assert effort.build_total == 23.0  # 10 + 5 + 8

    def test_overhead_total(self, minimal_phase: Phase) -> None:
        effort = minimal_phase.compute_effort()
        assert effort.overhead_total == 25.0  # 15 + 10

    def test_authored_total_is_the_sum_of_its_operands(self, minimal_phase: Phase) -> None:
        """The split shown to a reader must add up to the total shown beside it."""
        effort = minimal_phase.compute_effort()
        assert effort.authored_total == effort.build_total + effort.overhead_total
        assert effort.authored_total == 48.0  # 23 build + 25 overhead

    def test_staffed_capacity_from_resource_plan(self, minimal_phase: Phase) -> None:
        effort = minimal_phase.compute_effort()
        # Sum of all stream capacities: (2+2+2+1) + (0.5*4) + (1+0.5) = 7+2+1.5 = 10.5
        assert effort.staffed_capacity == minimal_phase.resource_plan.total_capacity

    def test_staffed_capacity_is_not_the_authored_total(self, minimal_phase: Phase) -> None:
        """Two quantities, never one: capacity covers the effort, it does not equal it."""
        effort = minimal_phase.compute_effort()
        assert effort.staffed_capacity != effort.authored_total


class TestBuildDetailedRowsCountOnce:
    """Effort the Build register itemises is never added again as overhead."""

    @staticmethod
    def _phase() -> Phase:
        """A phase shaped like the scaffold: Design detailed in both registers.

        Build register: Design 30 + Frontend 35 + Backend 25 = 90.
        Project register: Design & Architecture 30 (the Design build group seen
        from the project side), Build Activities 60 (the rest of it), plus 10
        Infrastructure and 20 Testing of genuine overhead. Authored effort is
        120; the resource plan books 150 to deliver it.
        """
        return Phase(
            phase_id="P1",
            name="Delivery",
            description="",
            build_activities=[
                BuildActivity(activity_id="B1", group="Design", name="Architecture",
                              effort_md=30.0),
                BuildActivity(activity_id="B2", group="Frontend", name="UI",
                              effort_md=35.0),
                BuildActivity(activity_id="B3", group="Backend", name="API",
                              effort_md=25.0),
            ],
            project_activities=[
                ProjectActivity(group="Design & Architecture", stream="1.Design",
                                effort_md=30.0),
                ProjectActivity(group="Build Activities", stream="2.Dev",
                                effort_md=60.0),
                ProjectActivity(group="Infrastructure & DevOps", stream="2.Dev",
                                effort_md=10.0),
                ProjectActivity(group="Testing & QA", stream="3.Test",
                                effort_md=20.0),
            ],
        )

    def test_design_stream_is_not_counted_twice(self) -> None:
        effort = self._phase().compute_effort()
        assert effort.build_total == 90.0
        assert effort.overhead_total == 30.0  # infrastructure + testing only
        assert effort.authored_total == 120.0

    def test_overhead_rows_exclude_the_build_detailed_groups(self) -> None:
        effort = self._phase().compute_effort()
        labels = [name for name, _ in effort.overhead_rows]
        assert labels == ["Infrastructure & DevOps", "Testing & QA"]

    def test_overhead_rows_sum_to_the_overhead_total(self) -> None:
        effort = self._phase().compute_effort()
        assert sum(md for _, md in effort.overhead_rows) == effort.overhead_total


class TestProjectActivityBuildDetail:
    """Which project rows the Build register already itemises."""

    def test_build_activities_group_is_build_detailed(self) -> None:
        act = ProjectActivity(group="Build Activities", stream="2.Dev", effort_md=1.0)
        assert act.is_build_detailed

    def test_design_stream_is_build_detailed(self) -> None:
        act = ProjectActivity(group="Design & Architecture", stream="1.Design",
                              effort_md=1.0)
        assert act.is_build_detailed

    def test_other_streams_are_overhead(self) -> None:
        act = ProjectActivity(group="Testing & QA", stream="3.Test", effort_md=1.0)
        assert not act.is_build_detailed

    def test_a_design_named_group_outside_a_design_stream_is_overhead(self) -> None:
        """The Stream column resolves the convention; the group name does not."""
        act = ProjectActivity(group="Design Lead", stream="Architecture", effort_md=1.0)
        assert not act.is_build_detailed
