"""Regression tests for the assumption risk map slide.

The register is the signer's exposure. A slide that renders one impact tier of
it still reads as the whole register, so the omission understates the exposure
without ever saying it did. These tests hold the slide to the register: every
assumption reaches it, ordered by what rides on it, and a column that cannot fit
its rows says how many it keeps back.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.adapters.outbound.slidev.assumptions import (
    _MAX_ROWS_PER_COLUMN,
    _render_risk_map,
)
from engine.domain.model.aggregates.project import Project
from engine.domain.model.entities.assumption import Assumption
from engine.domain.model.value_objects.confidence import Confidence
from engine.domain.model.value_objects.config import ProjectConfig
from engine.domain.model.value_objects.impact import Impact


def _assumption(
    aid: str,
    confidence: Confidence,
    impact: Impact,
    title: str = "",
) -> Assumption:
    return Assumption(
        assumption_id=aid,
        group="Economy",
        assumption=f"{aid} full text",
        short_title=title or f"{aid} title",
        confidence=confidence,
        impact=impact,
    )


def _project(assumptions: list[Assumption]) -> Project:
    config = ProjectConfig(
        name="Test Project",
        short_name="Test",
        client="Test Client",
        author="TestCorp",
        description="A test project",
        date="August 2026",
    )
    return Project(config=config, assumptions=assumptions)


def _render(assumptions: list[Assumption], tmp_path: Path) -> str:
    filename = _render_risk_map(_project(assumptions), tmp_path)
    assert filename == "08-assumptions-risk.md"
    return (tmp_path / "pages" / filename).read_text(encoding="utf-8")


class TestEveryAssumptionReachesTheSlide:
    """Impact orders the rows; it does not gate them."""

    def test_medium_and_high_impact_rows_are_rendered(self, tmp_path: Path) -> None:
        content = _render(
            [
                _assumption("ECO-ASM-001", Confidence.MEDIUM, Impact.HIGH),
                _assumption("ECO-ASM-003", Confidence.LOW, Impact.MEDIUM),
                _assumption("BAT-ASM-001", Confidence.LOW, Impact.CRITICAL),
            ],
            tmp_path,
        )
        assert "ECO-ASM-001" in content
        assert "ECO-ASM-003" in content
        assert "BAT-ASM-001" in content

    def test_slide_renders_when_nothing_is_critical(self, tmp_path: Path) -> None:
        content = _render(
            [_assumption("PVP-ASM-001", Confidence.HIGH, Impact.LOW)],
            tmp_path,
        )
        assert "PVP-ASM-001" in content

    def test_no_assumptions_renders_no_slide(self, tmp_path: Path) -> None:
        assert _render_risk_map(_project([]), tmp_path) is None

    def test_header_states_the_whole_register(self, tmp_path: Path) -> None:
        content = _render(
            [
                _assumption("A1", Confidence.LOW, Impact.CRITICAL),
                _assumption("A2", Confidence.MEDIUM, Impact.MEDIUM),
                _assumption("A3", Confidence.HIGH, Impact.LOW),
            ],
            tmp_path,
        )
        assert "All 3 assumptions" in content
        assert "1 of critical impact" in content


class TestColumnsAndOrdering:
    """Confidence picks the column; impact orders the rows inside it."""

    @pytest.mark.parametrize(
        ("confidence", "action"),
        [
            (Confidence.LOW, "VALIDATE"),
            (Confidence.MEDIUM, "MONITOR"),
            (Confidence.HIGH, "ACCEPT"),
        ],
    )
    def test_confidence_picks_the_column(
        self, confidence: Confidence, action: str, tmp_path: Path
    ) -> None:
        content = _render([_assumption("A1", confidence, Impact.HIGH)], tmp_path)
        assert f"{action} (1)" in content

    def test_rows_are_ordered_by_impact_within_a_column(self, tmp_path: Path) -> None:
        content = _render(
            [
                _assumption("LOW-1", Confidence.LOW, Impact.LOW),
                _assumption("CRIT-1", Confidence.LOW, Impact.CRITICAL),
                _assumption("MED-1", Confidence.LOW, Impact.MEDIUM),
            ],
            tmp_path,
        )
        assert content.index("CRIT-1") < content.index("MED-1") < content.index("LOW-1")

    def test_each_row_carries_its_impact(self, tmp_path: Path) -> None:
        content = _render(
            [_assumption("A1", Confidence.MEDIUM, Impact.HIGH)], tmp_path
        )
        assert "| **A1** | A1 title | HIGH |" in content


class TestNothingIsDroppedSilently:
    """A column that cannot fit its rows says how many it keeps back."""

    def test_overflow_is_stated_on_the_slide(self, tmp_path: Path) -> None:
        overflow = 3
        content = _render(
            [
                _assumption(f"A{i:03d}", Confidence.LOW, Impact.HIGH)
                for i in range(_MAX_ROWS_PER_COLUMN + overflow)
            ],
            tmp_path,
        )
        assert f"VALIDATE ({_MAX_ROWS_PER_COLUMN + overflow})" in content
        assert f"_+{overflow} more, lower impact._" in content

    def test_a_full_column_states_no_overflow(self, tmp_path: Path) -> None:
        content = _render(
            [
                _assumption(f"A{i:03d}", Confidence.LOW, Impact.HIGH)
                for i in range(_MAX_ROWS_PER_COLUMN)
            ],
            tmp_path,
        )
        assert "more, lower impact" not in content


class TestTopRisks:
    """The advice line names its subjects, or says there are none."""

    def test_names_low_confidence_high_stake_ids(self, tmp_path: Path) -> None:
        content = _render(
            [
                _assumption("ECO-ASM-001", Confidence.LOW, Impact.CRITICAL),
                _assumption("ECO-ASM-002", Confidence.LOW, Impact.HIGH),
                _assumption("ECO-ASM-003", Confidence.HIGH, Impact.CRITICAL),
            ],
            tmp_path,
        )
        assert "**Top risks:** ECO-ASM-001, ECO-ASM-002." in content
        assert "ECO-ASM-003." not in content

    def test_says_none_rather_than_rendering_an_empty_line(self, tmp_path: Path) -> None:
        content = _render(
            [_assumption("A1", Confidence.HIGH, Impact.CRITICAL)], tmp_path
        )
        assert "**Top risks:** none." in content

    def test_a_long_list_gives_the_count_and_points_at_the_column(
        self, tmp_path: Path
    ) -> None:
        content = _render(
            [
                _assumption(f"A{i:03d}", Confidence.LOW, Impact.CRITICAL)
                for i in range(10)
            ],
            tmp_path,
        )
        assert "**Top risks:** 10 assumptions pair low confidence" in content
        assert "and 4 more in VALIDATE" in content
