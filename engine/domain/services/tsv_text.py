"""Pure transforms over TSV text: read a header, add or replace a row, add a column.

The engine edits a project's TSV files in place when it mints a phase, and
those edits must leave every other byte as the author wrote it. These helpers
therefore work on lines and tabs, never re-quoting or re-flowing the rows they
do not touch.
"""

from __future__ import annotations

import csv
import io

from engine.domain.exceptions.invalid_row_error import InvalidRowError

__all__ = [
    "append_row",
    "cells_for_row",
    "column_values",
    "has_column",
    "header_of",
    "id_column",
    "insert_column",
    "replace_row",
    "row_numbers",
    "row_write_header",
]

_TAB = "\t"
_BOM = "\ufeff"


def _lines(text: str) -> tuple[list[str], str]:
    """Split *text* into its lines and the line ending it uses."""
    ending = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(ending)
    if lines and lines[-1] == "":
        lines.pop()
    return lines, ending


def header_of(text: str) -> list[str]:
    """The column names on the first line of *text*."""
    lines, _ = _lines(text)
    return lines[0].removeprefix(_BOM).split(_TAB) if lines else []


def has_column(text: str, header: str) -> bool:
    """Whether the first line of *text* names the column *header*."""
    return header in header_of(text)


def column_values(text: str, header: str) -> list[str]:
    """The stripped values under *header*, one per data row (missing cells read empty)."""
    lines, _ = _lines(text)
    if not lines:
        return []
    columns = lines[0].removeprefix(_BOM).split(_TAB)
    if header not in columns:
        return []
    index = columns.index(header)
    values: list[str] = []
    for line in lines[1:]:
        cells = line.split(_TAB)
        values.append(cells[index].strip() if index < len(cells) else "")
    return values


def append_row(text: str, cells: list[str]) -> str:
    """Return *text* with *cells* appended as its last data row, in the file's line ending."""
    lines, ending = _lines(text)
    lines.append(_TAB.join(cells))
    return ending.join(lines) + ending


def replace_row(text: str, row: int, cells: list[str]) -> str:
    """Return *text* with its data row number *row* (1-based) replaced by *cells*.

    Every other line keeps its bytes, and the file keeps or lacks a final line
    break as it did.
    """
    lines, ending = _lines(text)
    if not 1 <= row < len(lines):
        raise IndexError(f"no data row {row}")
    lines[row] = _TAB.join(cells)
    return ending.join(lines) + (ending if text.endswith("\n") else "")


def row_numbers(text: str, header: str, value: str) -> list[int]:
    """The 1-based data-row numbers whose stripped *header* cell equals *value*."""
    return [i for i, cell in enumerate(column_values(text, header), start=1) if cell == value]


def id_column(header: list[str]) -> str | None:
    """The column that identifies a row: the first one named ``... ID`` (``Req ID``)."""
    return next((name for name in header if name.endswith(" ID")), None)


def cells_for_row(header: list[str], row: dict[str, str]) -> list[str]:
    """The cells of *row* in *header* order, or a ValueError naming what does not fit.

    A row names every header column exactly once, by its exact name, and no
    other; a cell holds no tab and no line break, which would split the row.
    """
    missing = [name for name in header if name not in row]
    unknown = [name for name in row if name not in header]
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing column(s) {missing}")
        if unknown:
            parts.append(f"unknown column(s) {unknown}")
        raise ValueError("; ".join(parts) + f"; the header is {header}")
    for name in header:
        value = row[name]
        if not isinstance(value, str):
            raise ValueError(f"column {name!r} holds a {type(value).__name__}, not text")
        if any(ch in value for ch in "\t\r\n"):
            raise ValueError(f"column {name!r} holds a tab or a line break")
    cells = [row[name] for name in header]
    read_back = next(csv.reader([_TAB.join(cells)], delimiter=_TAB), [])
    for name, cell, back in zip(header, cells, read_back, strict=False):
        if cell != back:
            raise ValueError(
                f"column {name!r} would read back as {back!r}: a cell that starts with"
                " a double quote opens a quoted field"
            )
    if len(read_back) != len(cells):
        raise ValueError("the row would not read back as the cells given")
    return cells


def _reads_as_split(text: str) -> bool:
    """Whether the engine's TSV reading of *text* agrees with the line-and-tab view.

    The row writes address rows by line and cells by tab, so no line may end in
    a stray carriage return or line feed (each line ends with the file's own
    line ending or, for the last line, with none), each line must read on its
    own, with or without its line ending, as the row the whole file reads
    there, and split into as many cells as that row has; the header and the ID
    column must read the same either way. Mixed or stray line endings, a lone
    carriage return, a quoted cell spanning lines, holding a tab, or left open
    at the end of the file, or a quoted header or ID cell would make the two
    views differ.
    """
    body = text.removeprefix(_BOM)
    lines, ending = _lines(body)
    try:
        records = list(csv.reader(io.StringIO(body, newline=""), delimiter=_TAB))
        alone = [next(csv.reader([line], delimiter=_TAB), []) for line in lines]
        ended = [next(csv.reader([line + ending], delimiter=_TAB), []) for line in lines]
    except csv.Error:
        return False
    if any(line.endswith(("\r", "\n")) for line in lines):
        return False
    split = [line.split(_TAB) if line else [] for line in lines]
    if records != alone or ended != alone or not split or split[0] != records[0]:
        return False
    if any(len(cells) != len(row) for cells, row in zip(split, records, strict=True)):
        return False
    key = id_column(split[0])
    if key is not None:
        index = split[0].index(key)
        for cells, row in zip(split[1:], records[1:], strict=True):
            if len(cells) > index and cells[index] != row[index]:
                return False
    return True


def row_write_header(path: str, text: str) -> list[str]:
    """The header of the TSV data file at *path* a row write applies to.

    Raises InvalidRowError for a path that is not a TSV file, a file with no
    header row, a header that repeats a column name, or a file whose rows, cell
    counts, header, or ID column the engine reads differently from its lines and
    tabs.
    """
    if not path.lower().endswith(".tsv"):
        raise InvalidRowError(path, "row writes apply to TSV data files only")
    header = header_of(text)
    if not any(name.strip() for name in header):
        raise InvalidRowError(path, "the file has no header row")
    repeated = sorted({name for name in header if header.count(name) > 1})
    if repeated:
        raise InvalidRowError(
            path, f"the header repeats column(s) {repeated}; rewrite the whole file"
        )
    if not _reads_as_split(text):
        raise InvalidRowError(
            path,
            "the file does not read back one row per line with the same cell count,"
            " header, and ID column (mixed or stray line endings, a lone carriage"
            " return, a quoted cell spanning lines or holding a tab, or a quoted header"
            " or ID cell); rewrite the whole file",
        )
    return header


def insert_column(text: str, header: str, *, before: str | None = None, fill: str = "") -> str:
    """Return *text* with a new column *header*, every data row filled with *fill*.

    The column goes before the column named *before* when that column exists,
    otherwise at the end of the row.
    """
    lines, ending = _lines(text)
    if not lines:
        return header + ending
    columns = lines[0].split(_TAB)
    position = columns.index(before) if before is not None and before in columns else len(columns)
    out: list[str] = []
    for i, line in enumerate(lines):
        cells = line.split(_TAB)
        value = header if i == 0 else fill
        while len(cells) < position:
            cells.append("")
        cells.insert(position, value)
        out.append(_TAB.join(cells))
    return ending.join(out) + ending
