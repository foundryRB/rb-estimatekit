"""Integration tests for OpenpyxlExcelWriter.

Verifies the Excel writer produces workbooks from in-memory domain objects.
Some generators (quoter, financial) may fail without templates; the test
verifies partial success from the non-template generators.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.adapters.outbound.excel.excel_writer import OpenpyxlExcelWriter
from engine.adapters.outbound.excel.quoter.prepare import prepare_quoter
from engine.domain.exceptions import InvalidRateError
from engine.domain.model.aggregates.project import Project


class TestOpenpyxlExcelWriter:
    """End-to-end tests for OpenpyxlExcelWriter using minimal fixtures."""

    @pytest.fixture()
    def write_result(self, minimal_project: Project, tmp_path: Path) -> tuple[int, Path]:
        """Run the Excel writer and return (file_count, output_dir)."""
        count = OpenpyxlExcelWriter().write_all(minimal_project, tmp_path)
        return count, tmp_path

    def test_at_least_one_file_generated(self, write_result: tuple[int, Path]) -> None:
        """At least one Excel workbook must be produced."""
        count, out = write_result
        xlsx_files = list(out.glob("*.xlsx"))
        assert len(xlsx_files) >= 1

    def test_return_count_matches_files(self, write_result: tuple[int, Path]) -> None:
        """The returned count must match the number of .xlsx files on disk."""
        count, out = write_result
        xlsx_files = list(out.glob("*.xlsx"))
        assert count == len(xlsx_files)

    def test_return_count_positive(self, write_result: tuple[int, Path]) -> None:
        """The writer must return a positive file count."""
        count, _ = write_result
        assert count > 0

    def test_xlsx_files_are_non_empty(self, write_result: tuple[int, Path]) -> None:
        """Every generated .xlsx file must have non-zero size."""
        _, out = write_result
        for xlsx in out.glob("*.xlsx"):
            assert xlsx.stat().st_size > 0, f"{xlsx.name} is empty"

    def test_requirements_workbook_exists(self, write_result: tuple[int, Path]) -> None:
        """The Requirements workbook should always be generated."""
        _, out = write_result
        xlsx_files = [f.name.lower() for f in out.glob("*.xlsx")]
        has_req = any("requirement" in name for name in xlsx_files)
        assert has_req, f"No requirements workbook found among: {xlsx_files}"


class TestPrepareQuoter:
    """Quoter data extraction parses rates and fractional days from raw rows."""

    @pytest.fixture()
    def project_with_rows(self, minimal_project: Project) -> Project:
        minimal_project.phases[0].resource_rows = [
            {
                "Stream": "Delivery", "Profile": "Senior Dev", "Rate Day": "EUR 350",
                "M1": "1.5", "M2": "2", "M3": "0", "M4": "0",
            },
        ]
        return minimal_project

    def test_currency_prefixed_rate_is_parsed(self, project_with_rows: Project) -> None:
        data = prepare_quoter(project_with_rows, project_with_rows.phases[0])
        assert data is not None
        row = data.plan[0][1]
        assert row is not None
        assert row.rate == 350.0

    def test_fractional_days_are_preserved(self, project_with_rows: Project) -> None:
        data = prepare_quoter(project_with_rows, project_with_rows.phases[0])
        assert data is not None
        row = data.plan[0][1]
        assert row is not None
        assert row.days[0] == 1.5

    def test_unparsable_rate_raises_invalid_rate_error(
        self, project_with_rows: Project,
    ) -> None:
        phase = project_with_rows.phases[0]
        phase.resource_rows[0]["Rate Day"] = "TBD"
        with pytest.raises(InvalidRateError) as excinfo:
            prepare_quoter(project_with_rows, phase)
        assert "TBD" in str(excinfo.value)
