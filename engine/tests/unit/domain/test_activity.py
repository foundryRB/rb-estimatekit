"""Tests for Activity entities."""

from __future__ import annotations

from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.value_objects.requirement_id import RequirementId
from engine.domain.model.value_objects.resource_plan import ResourcePlan


class TestBuildActivity:
    def test_is_traced_when_has_req_ids(self) -> None:
        act = BuildActivity(
            activity_id="B1", group="Core", name="Test",
            effort_md=5.0, req_ids={RequirementId("R1")},
        )
        assert act.is_traced is True

    def test_not_traced_when_empty(self) -> None:
        act = BuildActivity(
            activity_id="B1", group="Core", name="Test",
            effort_md=5.0,
        )
        assert act.is_traced is False


class TestResourcePlan:
    def test_n_months(self) -> None:
        plan = ResourcePlan(streams={"Dev": [1.0, 2.0, 3.0], "QA": [0.5, 0.5]})
        assert plan.n_months == 3

    def test_total_capacity(self) -> None:
        plan = ResourcePlan(streams={"Dev": [1.0, 2.0], "QA": [0.5, 0.5]})
        assert plan.total_capacity == 4.0

    def test_empty_plan(self) -> None:
        plan = ResourcePlan()
        assert plan.n_months == 0
        assert plan.total_capacity == 0.0

    def test_stream_total(self) -> None:
        plan = ResourcePlan(streams={"Dev": [1.0, 2.0, 3.0]})
        assert plan.stream_total("Dev") == 6.0
        assert plan.stream_total("Unknown") == 0.0
