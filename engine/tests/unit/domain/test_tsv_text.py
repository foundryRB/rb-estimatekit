"""Tests for the TSV text transforms the engine applies to a project's own files."""

from __future__ import annotations

import pytest

from engine.domain.services.tsv_text import (
    append_row,
    cells_for_row,
    column_values,
    has_column,
    header_of,
    id_column,
    insert_column,
    replace_row,
    row_numbers,
)

_MATRIX = "Category\tReq ID\tPhase 1\tNotes\nAuth\tAUTH-001\t✓\tfirst\nDash\tDASH-001\t\t\n"


class TestReading:
    def test_header_and_column_values(self) -> None:
        assert header_of(_MATRIX) == ["Category", "Req ID", "Phase 1", "Notes"]
        assert column_values(_MATRIX, "Req ID") == ["AUTH-001", "DASH-001"]
        assert has_column(_MATRIX, "Notes")
        assert not has_column(_MATRIX, "Phase 2")

    def test_a_missing_column_reads_empty(self) -> None:
        assert column_values(_MATRIX, "Phase 2") == []
        assert header_of("") == []


class TestAppendRow:
    def test_appends_after_the_last_row_and_keeps_the_trailing_newline(self) -> None:
        text = append_row(_MATRIX, ["Int", "INT-001", "", ""])
        assert text.endswith("Int\tINT-001\t\t\n")
        assert text.startswith(_MATRIX)

    def test_a_file_without_a_trailing_newline_gains_one(self) -> None:
        text = append_row("A\tB\n1\t2", ["3", "4"])
        assert text == "A\tB\n1\t2\n3\t4\n"


class TestInsertColumn:
    def test_inserts_before_the_named_column_with_the_fill(self) -> None:
        text = insert_column(_MATRIX, "Phase 2", before="Notes", fill="")
        assert header_of(text) == ["Category", "Req ID", "Phase 1", "Phase 2", "Notes"]
        assert column_values(text, "Notes") == ["first", ""]
        assert column_values(text, "Phase 2") == ["", ""]

    def test_appends_at_the_end_when_no_anchor_is_named(self) -> None:
        text = insert_column("Group\tGuideline\nA\tOne\n", "Phase IDs", fill="All")
        assert header_of(text) == ["Group", "Guideline", "Phase IDs"]
        assert column_values(text, "Phase IDs") == ["All"]

    def test_preserves_windows_line_endings(self) -> None:
        text = insert_column("A\tB\r\n1\t2\r\n", "C", fill="x")
        assert text == "A\tB\tC\r\n1\t2\tx\r\n"


class TestRows:
    def test_replace_row_swaps_one_line_and_keeps_the_rest(self) -> None:
        text = replace_row(_MATRIX, 2, ["Dash", "DASH-001", "✓", "now P1"])
        assert text == (
            "Category\tReq ID\tPhase 1\tNotes\n"
            "Auth\tAUTH-001\t✓\tfirst\n"
            "Dash\tDASH-001\t✓\tnow P1\n"
        )

    def test_replace_row_keeps_crlf(self) -> None:
        crlf = _MATRIX.replace("\n", "\r\n")
        assert replace_row(crlf, 1, ["A", "B", "C", "D"]).endswith("\r\nDash\tDASH-001\t\t\r\n")

    def test_replace_row_refuses_a_row_that_does_not_exist(self) -> None:
        with pytest.raises(IndexError):
            replace_row(_MATRIX, 3, ["x"])

    def test_row_numbers_and_id_column(self) -> None:
        assert row_numbers(_MATRIX, "Req ID", "DASH-001") == [2]
        assert row_numbers(_MATRIX, "Req ID", "NOPE") == []
        assert id_column(header_of(_MATRIX)) == "Req ID"
        assert id_column(["Phase", "Phase ID", "Name"]) == "Phase ID"
        assert id_column(["Parameter", "Value"]) is None

    def test_replace_keeps_a_missing_final_break_missing(self) -> None:
        assert replace_row("A\tB\n1\t2", 1, ["9", "9"]) == "A\tB\n9\t9"

    def test_a_byte_order_mark_is_not_part_of_the_first_column_name(self) -> None:
        text = "\ufeffCategory\tReq ID\nAuth\tAUTH-001\n"
        assert header_of(text) == ["Category", "Req ID"]
        assert column_values(text, "Category") == ["Auth"]

    def test_cells_for_row_orders_by_header(self) -> None:
        header = ["Category", "Req ID", "Notes"]
        row = {"Notes": "n", "Category": "c", "Req ID": "R-1"}
        assert cells_for_row(header, row) == ["c", "R-1", "n"]

    @pytest.mark.parametrize(
        ("row", "reason"),
        [
            ({"Category": "c", "Req ID": "R-1"}, "missing column"),
            ({"Category": "c", "Req ID": "R-1", "Notes": "", "X": ""}, "unknown column"),
            ({"Category": "c", "Req ID": "R-1", "Notes": "a\tb"}, "tab or a line break"),
            ({"Category": "c", "Req ID": "R-1", "Notes": "a\r\nb"}, "tab or a line break"),
            ({"Category": "c", "Req ID": "R-1", "Notes": 3}, "not text"),
            ({"Category": '"c" d', "Req ID": "R-1", "Notes": ""}, "read back"),
        ],
    )
    def test_cells_for_row_refuses_what_does_not_fit(self, row: dict, reason: str) -> None:
        with pytest.raises(ValueError, match=reason):
            cells_for_row(["Category", "Req ID", "Notes"], row)
