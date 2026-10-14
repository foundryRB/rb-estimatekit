"""Tests for the rows a phase brings when minted."""

from __future__ import annotations

from engine.domain.services.phase_files import (
    EXAMPLE_SENTINEL,
    PHASE_ID_PATTERN,
    phase_display_name,
    phase_table_row,
)


class TestPhaseIds:
    def test_the_pattern_accepts_p_numbers_only(self) -> None:
        assert PHASE_ID_PATTERN.match("P1")
        assert PHASE_ID_PATTERN.match("P12")
        assert not PHASE_ID_PATTERN.match("Demo")
        assert not PHASE_ID_PATTERN.match("P1-build")
        assert not PHASE_ID_PATTERN.match("p2")

    def test_display_name_is_the_matrix_column_header(self) -> None:
        assert phase_display_name("P3") == "Phase 3"


class TestPhaseTableRow:
    def test_follows_the_files_header_and_marks_every_authored_value(self) -> None:
        header = ["Phase", "Phase ID", "Name", "Description", "Integration Type", "Examples"]
        row = phase_table_row(header, "P3")
        assert row[:2] == ["Phase 3", "P3"]
        assert all(cell.startswith(EXAMPLE_SENTINEL) for cell in row[2:])

    def test_unknown_columns_stay_empty(self) -> None:
        assert phase_table_row(["Phase ID", "Owner"], "P4") == ["P4", ""]
