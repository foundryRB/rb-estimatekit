"""Tests for auditor activity helpers (fractional man-day parsing)."""

from __future__ import annotations

from pytest_intent import intent

from auditor.checks.activity.helpers import (
    overloaded_month_cells,
    parse_md,
    resource_grand_total,
    resource_total_by_stream,
    stream_effort,
)


class TestParseMd:
    """Man-day values parse as floats, including fractional efforts."""

    def test_parses_fractional_values(self) -> None:
        assert parse_md("1.5") == 1.5

    def test_parses_whole_values(self) -> None:
        assert parse_md("3") == 3.0

    def test_empty_and_none_are_zero(self) -> None:
        assert parse_md("") == 0.0
        assert parse_md("  ") == 0.0
        assert parse_md(None) == 0.0


class TestFractionalSums:
    """Capacity and effort sums keep fractional man-days."""

    resource_rows = [
        {"Stream": "Delivery", "Profile": "Dev", "Rate Day": "350", "M1": "1.5", "M2": "2"},
        {"Stream": "QA", "Profile": "Tester", "Rate Day": "300", "M1": "0.5", "M2": ""},
    ]

    def test_resource_grand_total_includes_fractions(self) -> None:
        assert resource_grand_total(self.resource_rows) == 4.0

    def test_resource_total_by_stream_includes_fractions(self) -> None:
        assert resource_total_by_stream(self.resource_rows, "Delivery") == 3.5

    def test_stream_effort_includes_fractions(self) -> None:
        project_rows = [
            {"Stream": "Delivery", "Effort (MD)": "1.5"},
            {"Stream": "Delivery", "Effort (MD)": "2"},
            {"Stream": "QA", "Effort (MD)": "4"},
        ]
        assert stream_effort(project_rows, "Delivery") == 3.5


class TestOverloadedMonthCells:
    """A staffing line may not exceed DAYS_PER_MONTH (20) man-days in a month."""

    @intent("INT-ESTIMATEKIT-012")
    def test_flags_cells_over_the_ceiling(self) -> None:
        """Cells above 20 are reported as (stream, profile, month, value)."""
        rows = [
            {"Stream": "2.Dev", "Profile": "BE", "Rate Day": "260",
             "M1": "20", "M2": "21", "M3": "30"},
        ]
        assert overloaded_month_cells(rows) == [
            ("2.Dev", "BE", "M2", 21.0),
            ("2.Dev", "BE", "M3", 30.0),
        ]

    @intent("INT-ESTIMATEKIT-012")
    def test_twenty_and_below_are_within_capacity(self) -> None:
        """A full month (20) and anything under it are not flagged; empty is zero."""
        rows = [
            {"Stream": "2.Dev", "Profile": "BE", "Rate Day": "260",
             "M1": "20", "M2": "0", "M3": ""},
            {"Stream": "0.Lead", "Profile": "DM", "Rate Day": "360",
             "M1": "8", "M2": "8", "M3": "8"},
        ]
        assert overloaded_month_cells(rows) == []
