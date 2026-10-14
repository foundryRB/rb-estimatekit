"""Requirement ID parsing and requirements matrix reading."""

from __future__ import annotations

from pathlib import Path

from auditor.tsv import read_tsv

__all__ = [
    "MATRIX_FIXED_COLUMNS",
    "parse_req_ids",
    "read_requirements_matrix",
    "req_ids_cell_problem",
]

MATRIX_FIXED_COLUMNS = ("Category", "Req ID", "Description", "Notes")
"""The requirements matrix columns that are not phases: every other column is one."""


def parse_req_ids(text: str) -> set[str]:
    """Parse a comma-separated ``Req IDs`` cell into the set of its IDs.

    Returns the stripped, non-empty tokens. The sentinel value ``"All"`` is
    preserved: callers decide how to handle it. A cell that breaks the grammar
    is reported by :func:`req_ids_cell_problem`.
    """
    if not text or not text.strip():
        return set()
    return {p.strip() for p in text.split(",") if p.strip()}


def req_ids_cell_problem(cell: str) -> str | None:
    """Why a ``Req IDs`` cell breaks the grammar the engine reads, or None.

    A cell is comma-separated Req IDs, or ``All`` alone (any case). The engine
    splits on commas only, so a ``;`` joins two IDs into one unknown ID, an
    empty entry reads as an empty ID, and ``All`` beside a Req ID reads as one
    more Req ID instead of cross-cutting work. ``All`` stands alone, so a
    repeated ``All`` is refused too. A blank or ``N/A`` cell is not a grammar
    problem; the checks that require Req IDs refuse it.
    """
    text = cell.strip()
    if not text or text.upper() == "N/A":
        return None
    if ";" in text:
        return "uses ';': separate Req IDs with commas"
    tokens = [t.strip() for t in text.split(",")]
    if any(not t for t in tokens):
        return "has an empty entry: remove the stray comma"
    if len(tokens) > 1 and any(t.lower() == "all" for t in tokens):
        return "names 'All' beside other entries: 'All' stands alone"
    return None


def read_requirements_matrix(
    matrix_path: Path,
    phase_name: str,
) -> dict[str, dict[str, str]]:
    """Read requirements assigned to *phase_name* from the requirements matrix.

    Returns ``{req_id: {"description": ..., "category": ...}}``.
    """
    rows = read_tsv(matrix_path)
    reqs: dict[str, dict[str, str]] = {}
    for row in rows:
        req_id = row.get("Req ID", "").strip()
        phase_val = row.get(phase_name, "").strip()
        if req_id and phase_val:
            reqs[req_id] = {
                "description": row.get("Description", ""),
                "category": row.get("Category", ""),
            }
    return reqs
