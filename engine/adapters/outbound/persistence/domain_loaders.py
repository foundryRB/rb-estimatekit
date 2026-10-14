"""Loaders: assumptions and guidelines (the project-scoped registers)."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.persistence.requirement_loaders import parse_req_ids_raw
from engine.adapters.outbound.persistence.tsv_io import read_tsv
from engine.domain.constants.columns import (
    COL_ASSUMPTION,
    COL_ASSUMPTION_ID,
    COL_CONFIDENCE,
    COL_DESCRIPTION,
    COL_GROUP,
    COL_GUIDELINE,
    COL_GUIDELINE_ID,
    COL_ID,
    COL_IMPACT,
    COL_NAME,
    COL_PHASE_IDS,
    COL_REQ_IDS,
    COL_SHORT_TITLE,
)
from engine.domain.constants.files.inputs import FILE_ASSUMPTIONS, FILE_GUIDELINES
from engine.domain.model.entities.assumption import Assumption
from engine.domain.model.entities.guideline import ALL_PHASES, Guideline
from engine.domain.model.value_objects.confidence import Confidence
from engine.domain.model.value_objects.impact import Impact
from engine.domain.model.value_objects.requirement_id import RequirementId

__all__ = [
    "load_assumptions",
    "load_guidelines",
]


def load_assumptions(data_dir: Path) -> list[Assumption]:
    """Load assumptions/02-assumptions.tsv → list[Assumption]."""
    path = data_dir / FILE_ASSUMPTIONS
    if not path.exists():
        return []
    rows = read_tsv(path)
    result: list[Assumption] = []
    for row in rows:
        try:
            confidence = Confidence(row.get(COL_CONFIDENCE, "MEDIUM").strip().upper())
        except ValueError:
            confidence = Confidence.MEDIUM
        try:
            impact = Impact(row.get(COL_IMPACT, "MEDIUM").strip().upper())
        except ValueError:
            impact = Impact.MEDIUM
        result.append(Assumption(
            assumption_id=row.get(COL_ASSUMPTION_ID, ""),
            group=row.get(COL_GROUP, ""),
            assumption=row.get(COL_ASSUMPTION, ""),
            short_title=row.get(COL_SHORT_TITLE, ""),
            confidence=confidence,
            impact=impact,
            req_ids={RequirementId(r) for r in parse_req_ids_raw(row.get(COL_REQ_IDS, ""))},
        ))
    return result


def _parse_phase_ids(raw: str | None) -> frozenset[str]:
    """The phases a guideline row governs; an absent or empty cell governs them all."""
    tokens = {t.strip() for t in (raw or "").replace(";", ",").split(",") if t.strip()}
    return frozenset(tokens) if tokens else frozenset({ALL_PHASES})


def load_guidelines(data_dir: Path) -> list[Guideline]:
    """Load architecture/00-guidelines.tsv → list[Guideline]."""
    path = data_dir / FILE_GUIDELINES
    if not path.exists():
        return []
    rows = read_tsv(path)
    return [
        Guideline(
            guideline_id=row.get(COL_ID, row.get(COL_GUIDELINE_ID, "")),
            group=row.get(COL_GROUP, ""),
            name=row.get(COL_NAME, row.get(COL_GUIDELINE, "")),
            description=row.get(COL_DESCRIPTION, ""),
            phase_ids=_parse_phase_ids(row.get(COL_PHASE_IDS)),
        )
        for row in rows
    ]
