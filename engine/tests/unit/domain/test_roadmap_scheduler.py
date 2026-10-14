"""Tests for the roadmap scheduler build view (stream naming and capacity)."""

from __future__ import annotations

import pytest

from engine.domain.exceptions import SchedulingError
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.value_objects.resource_plan import ResourcePlan


class TestBuildCapacityStreamNaming:
    """Build capacity honors any stream naming, preferring the '2.Dev*' convention."""

    def test_plain_stream_names_schedule_a_roadmap(self, minimal_phase: Phase) -> None:
        # minimal_phase uses plain names (Development, Management, Architecture)
        roadmap = minimal_phase.schedule_roadmap()
        assert any(any(flags) for flags in roadmap.build_active.values())

    def test_dev_prefixed_streams_bound_build_capacity(self, minimal_phase: Phase) -> None:
        # 23 MD of build effort against 1 MD/month dev capacity fills all 12
        # months; the 10 MD/month non-dev stream is not build capacity.
        minimal_phase.resource_plan = ResourcePlan(
            streams={"2.Dev": [1.0] * 12, "3.PM": [10.0] * 12}
        )
        roadmap = minimal_phase.schedule_roadmap()
        flags = roadmap.build_active["Unmatched"]
        assert sum(flags) == 12

    def test_all_streams_carry_capacity_without_the_convention(
        self, minimal_phase: Phase,
    ) -> None:
        # Same monthly totals as above, but plain names: 11 MD/month build
        # capacity places the 23 MD of effort in 3 months.
        minimal_phase.resource_plan = ResourcePlan(
            streams={"Delivery": [1.0] * 12, "Support": [10.0] * 12}
        )
        roadmap = minimal_phase.schedule_roadmap()
        flags = roadmap.build_active["Unmatched"]
        assert sum(flags) == 3


class TestZeroBuildCapacity:
    """Build effort with no capacity fails with a domain error, not ZeroDivisionError."""

    def test_zero_capacity_with_effort_raises_scheduling_error(
        self, minimal_phase: Phase,
    ) -> None:
        minimal_phase.resource_plan = ResourcePlan(streams={"Delivery": [0.0] * 4})
        with pytest.raises(SchedulingError) as excinfo:
            minimal_phase.schedule_roadmap()
        assert "2.Dev" in str(excinfo.value)
