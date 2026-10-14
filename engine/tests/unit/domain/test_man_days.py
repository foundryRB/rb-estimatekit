"""Tests for the man-day text form.

The rule the format exists to hold: a figure is shown at the precision it
carries, so a part is never a rounded stand-in sitting beside an unrounded
total. Round the parts to whole days and leave the total alone and a column of
30s comes to sit under a total of 91, which is what a reader checking the
arithmetic finds wrong.
"""

from __future__ import annotations

import pytest

from engine.domain.model.value_objects.man_days import format_md


class TestPrecisionCarried:
    """Whole days render whole; a fraction keeps its decimal."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0.0, "0"),
            (30.0, "30"),
            (30.5, "30.5"),
            (0.5, "0.5"),
            (91.5, "91.5"),
            (1084.0, "1084"),
            (0.25, "0.25"),
            (30.1, "30.1"),
        ],
    )
    def test_renders_at_the_precision_carried(self, value: float, expected: str) -> None:
        assert format_md(value) == expected

    def test_float_noise_does_not_leak_a_decimal(self) -> None:
        assert format_md(0.1 + 0.2 + 0.2 + 0.2 + 0.3 + 29.0) == "30"

    def test_trailing_zeros_are_trimmed(self) -> None:
        assert format_md(30.10) == "30.1"
        assert format_md(100.0) == "100"


class TestDisplayedTotalsClose:
    """The reported defect: displayed parts must sum to the displayed total."""

    @pytest.mark.parametrize(
        "parts",
        [
            [30.0, 30.5, 30.5],   # the reported case: rows read 90, total read 91
            [30.5, 30.5, 30.5],   # the wider gap: rows read 90, total read 92
            [31.5, 31.5, 10.0],   # where truncation and rounding disagreed
            [0.5, 0.5],
            [10.0, 20.0, 30.0],
        ],
    )
    def test_parts_sum_to_the_total_as_displayed(self, parts: list[float]) -> None:
        displayed_parts = [float(format_md(p)) for p in parts]
        displayed_total = float(format_md(sum(parts)))
        assert sum(displayed_parts) == pytest.approx(displayed_total)

    def test_half_days_survive_instead_of_vanishing(self) -> None:
        """A half-day cell rendered as a whole day is effort the reader never sees."""
        assert format_md(0.5) != "0"
