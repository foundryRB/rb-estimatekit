"""Row-level writes to a project's TSV data files (append, replace by ID).

A follow-on adds or corrects a few rows without re-sending the file: every other
byte stays as the author wrote it, every row is checked against the header row
(the parsing contract), and a refused call writes nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.container import Container
from engine.domain.exceptions import DataFileNotFoundError, InvalidRowError
from engine.domain.services.tsv_text import row_write_header

_BRD = "data/requirements/01-brd.tsv"
_CONFIG = "data/activities/P1-config.tsv"


@pytest.fixture
def project(tmp_path: Path) -> tuple[Container, Path]:
    c = Container(projects_root=tmp_path)
    c.scaffold_project().execute(projects_root=tmp_path, slug="acme", force=False)
    return c, tmp_path / "acme"


def _bytes(path: Path, rel: str) -> bytes:
    return (path / rel).read_bytes()


def _row(**cells: str) -> dict[str, str]:
    base = {
        "Category": "Auth",
        "Req ID": "AUTH-002",
        "Description": "Single sign-on",
        "Original Text": "Users sign in once",
        "Lines": "2",
    }
    base.update(cells)
    return base


class TestAppend:
    def test_appends_after_the_last_row_and_keeps_every_other_byte(
        self, project: tuple[Container, Path]
    ) -> None:
        c, path = project
        before = _bytes(path, _BRD)
        rows = [_row(), _row(**{"Req ID": "AUTH-003"})]
        count = c.append_project_rows().execute(path, _BRD, rows)
        after = _bytes(path, _BRD)
        assert count == 2
        assert after.startswith(before)
        added = after[len(before):].decode("utf-8").splitlines()
        assert added == [
            "Auth\tAUTH-002\tSingle sign-on\tUsers sign in once\t2",
            "Auth\tAUTH-003\tSingle sign-on\tUsers sign in once\t2",
        ]

    @pytest.mark.parametrize(
        ("rows", "reason"),
        [
            ([{"Category": "Auth"}], "missing column"),
            ([{**_row(), "Priority": "High"}], "unknown column"),
            ([_row(Description="split\there")], "tab or a line break"),
            ([_row(Description="two\nlines")], "tab or a line break"),
            ([_row(), {"Req ID": "AUTH-003"}], "row 2"),
            ([], "no rows"),
        ],
    )
    def test_a_row_that_does_not_fit_the_header_writes_nothing(
        self, project: tuple[Container, Path], rows: list[dict[str, str]], reason: str
    ) -> None:
        c, path = project
        before = _bytes(path, _BRD)
        with pytest.raises(InvalidRowError, match=reason):
            c.append_project_rows().execute(path, _BRD, rows)
        assert _bytes(path, _BRD) == before

    def test_only_tsv_data_files_take_rows(self, project: tuple[Container, Path]) -> None:
        c, path = project
        with pytest.raises(InvalidRowError, match="TSV"):
            c.append_project_rows().execute(path, "project.yaml", [{"name": "x"}])

    def test_a_missing_file_is_reported(self, project: tuple[Container, Path]) -> None:
        c, path = project
        with pytest.raises(DataFileNotFoundError):
            c.append_project_rows().execute(path, "data/requirements/09-none.tsv", [_row()])


class TestReplace:
    def test_replaces_the_one_row_with_that_id_and_keeps_every_other_line(
        self, project: tuple[Container, Path]
    ) -> None:
        c, path = project
        before = _bytes(path, _BRD).decode("utf-8").splitlines()
        target = next(i for i, line in enumerate(before) if "\tAUTH-001\t" in line)
        row = _row(**{"Req ID": "AUTH-001", "Description": "MFA for every user", "Lines": "15"})
        c.replace_project_row().execute(path, _BRD, "AUTH-001", row)
        after = _bytes(path, _BRD).decode("utf-8").splitlines()
        assert len(after) == len(before)
        assert after[target] == "Auth\tAUTH-001\tMFA for every user\tUsers sign in once\t15"
        assert [line for i, line in enumerate(after) if i != target] == [
            line for i, line in enumerate(before) if i != target
        ]

    @pytest.mark.parametrize(
        ("row_id", "row", "reason"),
        [
            ("NOPE-001", _row(**{"Req ID": "NOPE-001"}), "no row with Req ID 'NOPE-001'"),
            ("AUTH-001", _row(**{"Req ID": "AUTH-009"}), "must stay 'AUTH-001'"),
            ("AUTH-001", {"Req ID": "AUTH-001"}, "missing column"),
        ],
    )
    def test_a_replace_that_does_not_fit_writes_nothing(
        self,
        project: tuple[Container, Path],
        row_id: str,
        row: dict[str, str],
        reason: str,
    ) -> None:
        c, path = project
        before = _bytes(path, _BRD)
        with pytest.raises(InvalidRowError, match=reason):
            c.replace_project_row().execute(path, _BRD, row_id, row)
        assert _bytes(path, _BRD) == before

    def test_several_rows_with_the_id_are_refused(self, project: tuple[Container, Path]) -> None:
        c, path = project
        text = (path / _BRD).read_bytes().decode("utf-8")
        duplicate = "Auth\tAUTH-001\tCopy\tCopy\t1\n"
        c.write_project_file().execute(path, _BRD, text.replace("\r\n", "\n") + duplicate)
        before = _bytes(path, _BRD)
        with pytest.raises(InvalidRowError, match="2 rows"):
            c.replace_project_row().execute(path, _BRD, "AUTH-001", _row(**{"Req ID": "AUTH-001"}))
        assert _bytes(path, _BRD) == before

    def test_a_file_without_an_id_column_is_refused(self, project: tuple[Container, Path]) -> None:
        c, path = project
        row = {"Parameter": "Design Lead", "Value": "5", "Unit": "days", "Description": "x"}
        before = _bytes(path, _CONFIG)
        with pytest.raises(InvalidRowError, match="no ID column"):
            c.replace_project_row().execute(path, _CONFIG, "Design Lead", row)
        assert _bytes(path, _CONFIG) == before

    def test_a_blank_id_names_no_row(self, project: tuple[Container, Path]) -> None:
        c, path = project
        before = _bytes(path, _BRD)
        with pytest.raises(InvalidRowError, match="blank Req ID"):
            c.replace_project_row().execute(path, _BRD, "  ", _row(**{"Req ID": ""}))
        assert _bytes(path, _BRD) == before


_NOTES = "data/notes.tsv"
_HEADER = "Note ID\tText"


def _raw(path: Path, data: bytes) -> None:
    (path / _NOTES).write_bytes(data)


class TestBytes:
    """Untouched lines keep their exact bytes, whatever the file's line endings."""

    @pytest.mark.parametrize(
        ("original", "appended"),
        [
            (b"Note ID\tText\nN-1\ta\n", b"Note ID\tText\nN-1\ta\nN-2\tb\n"),
            (b"Note ID\tText\r\nN-1\ta\r\n", b"Note ID\tText\r\nN-1\ta\r\nN-2\tb\r\n"),
            (b"Note ID\tText\nN-1\ta", b"Note ID\tText\nN-1\ta\nN-2\tb\n"),
            (
                b"\xef\xbb\xbfNote ID\tText\nN-1\ta\n",
                b"\xef\xbb\xbfNote ID\tText\nN-1\ta\nN-2\tb\n",
            ),
        ],
        ids=["lf", "crlf", "no-final-break", "bom"],
    )
    def test_append(
        self, project: tuple[Container, Path], original: bytes, appended: bytes
    ) -> None:
        c, path = project
        _raw(path, original)
        c.append_project_rows().execute(path, _NOTES, [{"Note ID": "N-2", "Text": "b"}])
        assert _bytes(path, _NOTES) == appended

    @pytest.mark.parametrize(
        ("original", "replaced"),
        [
            (b"Note ID\tText\nN-1\ta\nN-2\tb\n", b"Note ID\tText\nN-1\tz\nN-2\tb\n"),
            (b"Note ID\tText\r\nN-1\ta\r\nN-2\tb\r\n", b"Note ID\tText\r\nN-1\tz\r\nN-2\tb\r\n"),
            (b"Note ID\tText\nN-2\tb\nN-1\ta", b"Note ID\tText\nN-2\tb\nN-1\tz"),
            (
                b"\xef\xbb\xbfNote ID\tText\nN-1\ta\nN-2\tb\n",
                b"\xef\xbb\xbfNote ID\tText\nN-1\tz\nN-2\tb\n",
            ),
        ],
        ids=["lf", "crlf", "no-final-break", "bom"],
    )
    def test_replace(
        self, project: tuple[Container, Path], original: bytes, replaced: bytes
    ) -> None:
        c, path = project
        _raw(path, original)
        c.replace_project_row().execute(path, _NOTES, "N-1", {"Note ID": "N-1", "Text": "z"})
        assert _bytes(path, _NOTES) == replaced


class TestRefusedShapes:
    @pytest.mark.parametrize("text", ['"Quoted" title', '"', '"a b"'])
    def test_a_cell_that_would_not_read_back_is_refused(
        self, project: tuple[Container, Path], text: str
    ) -> None:
        c, path = project
        _raw(path, b"Note ID\tText\nN-1\ta\n")
        before = _bytes(path, _NOTES)
        with pytest.raises(InvalidRowError, match="read back"):
            c.append_project_rows().execute(path, _NOTES, [{"Note ID": "N-2", "Text": text}])
        with pytest.raises(InvalidRowError, match="read back"):
            c.replace_project_row().execute(path, _NOTES, "N-1", {"Note ID": "N-1", "Text": text})
        assert _bytes(path, _NOTES) == before

    def test_a_quote_inside_a_cell_reads_back_and_is_kept(
        self, project: tuple[Container, Path]
    ) -> None:
        c, path = project
        _raw(path, b"Note ID\tText\nN-1\ta\n")
        c.append_project_rows().execute(path, _NOTES, [{"Note ID": "N-2", "Text": 'a "b" c'}])
        assert _bytes(path, _NOTES).endswith(b'N-2\ta "b" c\n')

    @pytest.mark.parametrize(
        "rows",
        [
            [{"Note ID": "N-1", "Text": "again"}],
            [{"Note ID": "N-2", "Text": "b"}, {"Note ID": "N-2", "Text": "c"}],
        ],
        ids=["already-in-file", "twice-in-call"],
    )
    def test_an_id_already_taken_is_refused(
        self, project: tuple[Container, Path], rows: list[dict[str, str]]
    ) -> None:
        c, path = project
        _raw(path, b"Note ID\tText\nN-1\ta\n")
        before = _bytes(path, _NOTES)
        with pytest.raises(InvalidRowError, match="already in the file|repeats an earlier row"):
            c.append_project_rows().execute(path, _NOTES, rows)
        assert _bytes(path, _NOTES) == before

    def test_a_repeat_within_the_call_is_named_as_one(
        self, project: tuple[Container, Path]
    ) -> None:
        c, path = project
        _raw(path, b"Note ID\tText\nN-1\ta\n")
        rows = [{"Note ID": "N-2", "Text": "b"}, {"Note ID": "N-2", "Text": "c"}]
        with pytest.raises(InvalidRowError, match="row 2: Note ID 'N-2' repeats an earlier row"):
            c.append_project_rows().execute(path, _NOTES, rows)

    def test_a_blank_id_is_refused_on_append(self, project: tuple[Container, Path]) -> None:
        c, path = project
        _raw(path, b"Note ID\tText\nN-1\ta\n")
        before = _bytes(path, _NOTES)
        with pytest.raises(InvalidRowError, match="blank Note ID"):
            c.append_project_rows().execute(path, _NOTES, [{"Note ID": " ", "Text": "b"}])
        assert _bytes(path, _NOTES) == before

    @pytest.mark.parametrize(
        "data",
        [
            b"Note ID\tText\r\nN-1\ta\nN-2\tb\r\nN-3\tc\r\n",
            b"Note ID\tText\nN-1\ta\rN-2\tb\n",
            b'Note ID\tText\nN-1\t"two\nlines"\nN-2\tb\n',
            b"Note ID\tText\r\nN-1\ta\r\nN-2\tb\n",
            b"Note ID\tText\nN-1\ta\nN-2\tb\r",
            b"Note ID\tText\r\nN-1\ta\r\nN-2\tb\r",
            b'Note ID\tText\nN-1\t"TBD',
        ],
        ids=[
            "mixed-endings",
            "lone-cr",
            "quoted-multiline-cell",
            "stray-final-lf",
            "stray-final-cr",
            "stray-final-cr-in-crlf",
            "quote-left-open-at-the-end",
        ],
    )
    def test_a_file_that_does_not_read_one_row_per_line_is_refused(
        self, project: tuple[Container, Path], data: bytes
    ) -> None:
        c, path = project
        _raw(path, data)
        replacement = {"Note ID": "N-1", "Text": "z"}
        with pytest.raises(InvalidRowError, match="one row per line"):
            c.replace_project_row().execute(path, _NOTES, "N-1", replacement)
        with pytest.raises(InvalidRowError, match="one row per line"):
            c.append_project_rows().execute(path, _NOTES, [{"Note ID": "N-9", "Text": "z"}])
        assert _bytes(path, _NOTES) == data

    def test_an_existing_cell_that_starts_with_a_quote_does_not_block_a_write(
        self, project: tuple[Container, Path]
    ) -> None:
        """Bundled data holds cells like '"Custom" order'; each line is still one row."""
        c, path = project
        _raw(path, b'Note ID\tText\nN-1\t"Custom" order\nN-2\tb\n')
        c.replace_project_row().execute(path, _NOTES, "N-2", {"Note ID": "N-2", "Text": "z"})
        assert _bytes(path, _NOTES) == b'Note ID\tText\nN-1\t"Custom" order\nN-2\tz\n'

    @pytest.mark.parametrize(
        "data",
        [
            b'Text\tNote ID\tMore\n"a\tN-2\tb"\tN-1\tc\nplain\tN-3\td\n',
            b'Note ID\tText\n"N-1"\ta\nN-2\tb\n',
            b'"Note ID"\tText\nN-1\ta\n',
        ],
        ids=["quoted-cell-holding-a-tab", "quoted-id-cell", "quoted-header-cell"],
    )
    def test_a_file_whose_cells_read_differently_is_refused(
        self, project: tuple[Container, Path], data: bytes
    ) -> None:
        c, path = project
        _raw(path, data)
        with pytest.raises(InvalidRowError, match="same cell count"):
            c.replace_project_row().execute(path, _NOTES, "N-2", {"Note ID": "N-2", "Text": "z"})
        with pytest.raises(InvalidRowError, match="same cell count"):
            c.append_project_rows().execute(path, _NOTES, [{"Note ID": "N-1", "Text": "z"}])
        assert _bytes(path, _NOTES) == data

    def test_a_header_that_repeats_a_column_is_refused(
        self, project: tuple[Container, Path]
    ) -> None:
        c, path = project
        data = b"Note ID\tText\tNote ID\nA\tx\tN-1\n"
        _raw(path, data)
        with pytest.raises(InvalidRowError, match="repeats column"):
            c.replace_project_row().execute(path, _NOTES, "A", {"Note ID": "A", "Text": "z"})
        with pytest.raises(InvalidRowError, match="repeats column"):
            c.append_project_rows().execute(path, _NOTES, [{"Note ID": "N-1", "Text": "z"}])
        assert _bytes(path, _NOTES) == data


_REPO = Path(__file__).resolve().parents[3]
_DATA_TSVS = sorted(
    [*(_REPO / "templates").rglob("*.tsv"), *(_REPO / "projects").glob("*/data/**/*.tsv")]
)


@pytest.mark.parametrize(
    "tsv", _DATA_TSVS, ids=[p.relative_to(_REPO).as_posix() for p in _DATA_TSVS]
)
def test_every_template_and_bundled_tsv_passes_the_row_write_check(tsv: Path) -> None:
    """The check refuses only files the engine reads differently; the repo's own data passes."""
    row_write_header(tsv.name, tsv.read_bytes().decode("utf-8"))
