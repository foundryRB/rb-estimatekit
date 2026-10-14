"""TSV structural validity: UTF-8, consistent columns, no empty files."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.tsv import read_tsv_raw

logger = logging.getLogger(__name__)


def _all_tsv_files(project_root: Path) -> list[Path]:
    """Return sorted list of all .tsv files in data/ subdirectories."""
    data_dir = project_root / "data"
    if not data_dir.exists():
        return []
    return sorted(data_dir.rglob("*.tsv"))


def test_all_tsv_files_are_valid_utf8(project_root: Path) -> None:
    """Every TSV in data/ is readable as UTF-8."""
    failures: list[str] = []
    for tsv in _all_tsv_files(project_root):
        try:
            tsv.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            failures.append(f"{tsv.name}: {e}")

    logger.info("Checked %d TSV files for UTF-8", len(_all_tsv_files(project_root)))
    assert not failures, "UTF-8 failures:\n  " + "\n  ".join(failures)


def test_all_tsv_files_have_consistent_columns(project_root: Path) -> None:
    """Every row in each TSV has the same number of columns as the header."""
    failures: list[str] = []
    for tsv in _all_tsv_files(project_root):
        rows = read_tsv_raw(tsv)
        if not rows:
            failures.append(f"{tsv.name}: empty file")
            continue
        header_len = len(rows[0])
        for i, row in enumerate(rows[1:], start=2):
            if len(row) != header_len:
                failures.append(
                    f"{tsv.name}:L{i}: {len(row)} cols (header has {header_len})"
                )

    logger.info("Checked column consistency in %d files", len(_all_tsv_files(project_root)))
    assert not failures, (
        f"{len(failures)} column mismatches:\n  " + "\n  ".join(failures[:20])
    )


def test_no_empty_tsv_files(project_root: Path) -> None:
    """No TSV in data/ is completely empty (0 data rows)."""
    empty: list[str] = []
    for tsv in _all_tsv_files(project_root):
        rows = read_tsv_raw(tsv)
        if len(rows) < 2:
            empty.append(tsv.name)

    assert not empty, "Empty TSV files (no data rows):\n  " + "\n  ".join(empty)
