"""TSV I/O primitives — low-level read/write for tab-separated files."""

from __future__ import annotations

import csv
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    """Read a TSV file and return rows as list of dicts.

    Uses the first row as headers. Strips BOM if present.
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    """Write rows to a TSV file with the given column headers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
