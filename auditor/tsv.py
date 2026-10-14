"""TSV file reading primitives."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

__all__ = ["read_tsv", "read_tsv_raw"]


def _require_file(path: Path) -> None:
    """Fail the calling check when *path* is absent, naming the file."""
    if not path.exists():
        pytest.fail(f"Required data file missing: {path}", pytrace=False)


def read_tsv(path: Path) -> list[dict[str, str]]:
    """Read a TSV file and return rows as a list of ``{column: value}`` dicts.

    A missing file fails the calling check with a message naming the file.
    """
    _require_file(path)
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def read_tsv_raw(path: Path) -> list[list[str]]:
    """Read a TSV file as raw rows (list of cell lists) via ``csv.reader``.

    A missing file fails the calling check with a message naming the file.
    """
    _require_file(path)
    with open(path, encoding="utf-8") as f:
        return list(csv.reader(f, delimiter="\t"))
