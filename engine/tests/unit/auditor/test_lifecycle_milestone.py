"""Tests for the Lifecycle build-milestone check.

Focus: with SIT and UAT both 0 and testing effort in the phase, the generator
ends each category's build block on the test milestone ▲ (acceptance completes
with the build) and draws no test window. The check accepts that end mark only
when the phase's config integrates testing (SIT and UAT both 0); with a test
window, one month or more, the build still ends on ◆.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from auditor.checks.roadmap.conftest import check_lifecycle_build_milestone_at_end
from engine.domain.model.value_objects.phase_config import PhaseConfig
from engine.domain.services.roadmap_scheduler._lifecycle import compute_lifecycle

_PATH = Path("Roadmap-LifecycleP1.tsv")


def _rows(*cells: str) -> list[dict[str, str]]:
    """One lifecycle data row over months M1.. with the given cells."""
    row = {"Category": "Dashboard", "Effort (MD)": "40", "Milestone": "Dashboard Complete"}
    row.update({f"M{i}": v for i, v in enumerate(cells, start=1)})
    return [row]


def _generated(config: PhaseConfig, *, has_testing_effort: bool) -> list[dict[str, str]]:
    """The rows the generator writes for one category building in M1-M2."""
    raw = compute_lifecycle(
        {"Dashboard": [True, True, False]}, 3, config, has_testing_effort=has_testing_effort,
    )
    return _rows(*raw["Dashboard"])


class TestGeneratorOutputPasses:
    def test_integrated_testing(self) -> None:
        rows = _generated(PhaseConfig(sit_days=0, uat_days=0), has_testing_effort=True)
        assert "▲" in rows[0].values()
        check_lifecycle_build_milestone_at_end(_PATH, rows, integrated_testing=True)

    def test_integrated_config_without_testing_effort(self) -> None:
        rows = _generated(PhaseConfig(sit_days=0, uat_days=0), has_testing_effort=False)
        assert "◆" in rows[0].values()
        check_lifecycle_build_milestone_at_end(_PATH, rows, integrated_testing=True)

    def test_test_window(self) -> None:
        rows = _generated(PhaseConfig(sit_days=20, uat_days=20), has_testing_effort=True)
        assert "T" in rows[0].values()
        check_lifecycle_build_milestone_at_end(_PATH, rows, integrated_testing=False)

    def test_one_month_test_window(self) -> None:
        rows = _generated(PhaseConfig(sit_days=10, uat_days=10), has_testing_effort=True)
        assert [rows[0][m] for m in ("M2", "M3")] == ["◆", "▲"]
        check_lifecycle_build_milestone_at_end(_PATH, rows, integrated_testing=False)


class TestMissingMilestoneFails:
    def test_build_ending_without_milestone(self) -> None:
        with pytest.raises(AssertionError, match="expected"):
            check_lifecycle_build_milestone_at_end(_PATH, _rows("·", "·", ""))

    def test_dropped_milestone_before_a_one_month_window(self) -> None:
        """With a test window configured, a lone ▲ never stands in for the build's ◆."""
        with pytest.raises(AssertionError, match="expected '◆'"):
            check_lifecycle_build_milestone_at_end(
                _PATH, _rows("·", "·", "▲"), integrated_testing=False,
            )

    def test_test_milestone_before_a_test_window(self) -> None:
        with pytest.raises(AssertionError, match="expected '◆'"):
            check_lifecycle_build_milestone_at_end(_PATH, _rows("·", "▲", "T"))
