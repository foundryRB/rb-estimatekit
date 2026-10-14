"""BRD-specific parsers for customer requirements and BRD line extraction."""

from __future__ import annotations

import contextlib
from pathlib import Path

from auditor.tsv import read_tsv

__all__ = [
    "read_brd_lines",
    "read_customer_requirements",
]


def read_customer_requirements(filepath: Path) -> dict[int, str]:
    """Extract the lines of the customer requirements file the BRD must cover.

    Every non-blank line is tracked: each one must be cited by at least one BRD
    row's Lines. Blank and whitespace-only lines are the only lines left out,
    so nothing depends on the input's formatting or language.
    Returns ``{line_number: stripped_text}`` for each tracked line.
    """
    with open(filepath, encoding="utf-8-sig") as f:
        lines = f.readlines()

    content_lines: dict[int, str] = {}
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped:
            content_lines[i] = stripped

    return content_lines


def read_brd_lines(filepath: Path) -> tuple[set[int], list[dict[str, str]]]:
    """Read BRD and return ``(covered_line_numbers, requirements_list)``."""
    covered: set[int] = set()
    requirements: list[dict[str, str]] = []

    for row in read_tsv(filepath):
        req: dict[str, str] = {
            "req_id": row.get("Req ID", ""),
            "lines": row.get("Lines", "").strip(),
        }
        requirements.append(req)

        lines_str = req["lines"]
        if lines_str and "-" in lines_str:
            parts = lines_str.split("-")
            try:
                for ln in range(int(parts[0]), int(parts[1]) + 1):
                    covered.add(ln)
            except ValueError:
                pass
        elif lines_str:
            for part in lines_str.split(","):
                with contextlib.suppress(ValueError):
                    covered.add(int(part.strip()))

    return covered, requirements
