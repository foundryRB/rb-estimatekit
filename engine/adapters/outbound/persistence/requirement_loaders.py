"""Loaders: requirements and BRD index from TSV files."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.persistence.tsv_io import read_tsv
from engine.domain.constants.columns import (
    COL_CATEGORY,
    COL_DESCRIPTION,
    COL_REQ_ID,
)
from engine.domain.constants.files.inputs import FILE_BRD, FILE_MATRIX
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.entities.requirement import Requirement
from engine.domain.model.value_objects.category import Category
from engine.domain.model.value_objects.requirement_id import RequirementId

__all__ = ["load_brd_index", "load_requirements", "parse_req_ids_raw"]


def parse_req_ids_raw(raw: str) -> set[str]:
    """Parse a Req IDs cell → set of string IDs.

    A cell is comma-separated Req IDs, or ``All`` alone (any case), which
    reads as ``{"ALL"}``, the cross-cutting sentinel. A blank or ``N/A`` cell
    names no requirement.
    """
    raw = raw.strip()
    if not raw or raw.upper() == "N/A":
        return set()
    if raw.upper() == "ALL":
        return {"ALL"}
    return {part.strip() for part in raw.split(",")}


def load_brd_index(data_dir: Path) -> tuple[list[str], dict[str, str]]:
    """Build BRD category index from requirements/01-brd.tsv."""
    path = data_dir / FILE_BRD
    if not path.exists():
        return [], {}
    rows = read_tsv(path)
    categories_order: list[str] = []
    req_to_cat: dict[str, str] = {}
    for row in rows:
        cat = row.get(COL_CATEGORY, "")
        req_id = row.get(COL_REQ_ID, "")
        req_to_cat[req_id] = cat
        if cat and cat not in categories_order:
            categories_order.append(cat)
    return categories_order, req_to_cat


def load_requirements(data_dir: Path, phases: list[Phase]) -> list[Requirement]:
    """Load requirements/01-brd.tsv + requirements/03-matrix.tsv → list[Requirement]."""
    brd_path = data_dir / FILE_BRD
    if not brd_path.exists():
        return []
    brd_rows = read_tsv(brd_path)

    # Build allocation map from RequirementsMatrix
    matrix_path = data_dir / FILE_MATRIX
    matrix: dict[str, dict[str, str]] = {}
    if matrix_path.exists():
        for row in read_tsv(matrix_path):
            req_id = row.get(COL_REQ_ID, "").strip()
            if req_id:
                matrix[req_id] = row

    requirements: list[Requirement] = []
    for row in brd_rows:
        req_id = row.get(COL_REQ_ID, "").strip()
        if not req_id:
            continue
        req = Requirement(
            id=RequirementId(req_id),
            category=Category(
                name=row.get(COL_CATEGORY, ""),
            ),
            description=row.get(COL_DESCRIPTION, ""),
        )
        # Phase allocations use the Phase column header ("Phase 1", "Demo")
        matrix_row = matrix.get(req_id, {})
        for phase in phases:
            alloc = matrix_row.get(phase.phase_name, "")
            if alloc:
                req.phase_allocations[phase.phase_id] = alloc
        requirements.append(req)
    return requirements
