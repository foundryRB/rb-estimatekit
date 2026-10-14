"""Activity file reading and requirement-mapping."""

from __future__ import annotations

from pathlib import Path

from auditor.requirements import parse_req_ids
from auditor.tsv import read_tsv

__all__ = ["activity_req_ids", "read_activities", "read_activity_req_map"]


def activity_req_ids(cell: str) -> set[str]:
    """The requirement IDs a build activity's ``Req IDs`` cell names.

    A cell that is exactly ``All`` (case-insensitive) marks a cross-cutting
    activity, whose effort the roadmap spreads across every category: it
    names no requirement, so the set is empty. Beside other IDs, ``All`` is
    one more token the roadmap reads as a Req ID, and it is returned with
    them for the reference checks to refuse.
    """
    req_ids = parse_req_ids(cell)
    if len(req_ids) == 1 and next(iter(req_ids)).lower() == "all":
        return set()
    return req_ids


def read_activities(build_path: Path) -> tuple[set[str], list[dict[str, str]]]:
    """Read a Build TSV and return ``(referenced_req_ids, activities)``.

    The referenced set unions every row's :func:`activity_req_ids`, so a
    whole-cell ``All`` contributes nothing.
    """
    rows = read_tsv(build_path)
    referenced: set[str] = set()
    for row in rows:
        referenced |= activity_req_ids(row.get("Req IDs", ""))
    return referenced, rows


def read_activity_req_map(
    build_path: Path,
) -> tuple[set[str], dict[str, list[str]]]:
    """Read a Build TSV and return ``(referenced_req_ids, req_to_activities)``.

    ``req_to_activities`` maps each requirement ID to the list of Activity IDs
    that reference it, read with :func:`activity_req_ids`.
    """
    rows = read_tsv(build_path)
    referenced: set[str] = set()
    req_to_acts: dict[str, list[str]] = {}
    for row in rows:
        act_id = row.get("Activity ID", "").strip()
        for rid in activity_req_ids(row.get("Req IDs", "")):
            referenced.add(rid)
            req_to_acts.setdefault(rid, []).append(act_id)
    return referenced, req_to_acts
