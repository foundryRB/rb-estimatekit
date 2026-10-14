"""Assumptions have valid Confidence and Impact values from their lookup tables."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_assumptions_have_valid_confidence(project_root: Path) -> None:
    """All assumptions have valid Confidence values."""
    confidence_path = get_data_file(project_root, "assumptions", "00-confidence.tsv")
    path = get_data_file(project_root, "assumptions", "02-assumptions.tsv")

    valid = {
        row.get("Confidence", "").strip()
        for row in read_tsv(confidence_path)
        if row.get("Confidence", "").strip()
    }
    invalid: list[tuple[str, str]] = []
    for row in read_tsv(path):
        aid = row.get("Assumption ID", "").strip()
        conf = row.get("Confidence", "").strip()
        if conf not in valid:
            invalid.append((aid, conf))

    logger.info("Valid confidence levels: %s", sorted(valid))
    assert len(invalid) == 0, f"{len(invalid)} invalid Confidence values"


def test_assumptions_have_valid_impact(project_root: Path) -> None:
    """All assumptions have valid Impact values."""
    impact_path = get_data_file(project_root, "assumptions", "01-impact.tsv")
    path = get_data_file(project_root, "assumptions", "02-assumptions.tsv")

    valid = {
        row.get("Impact", "").strip()
        for row in read_tsv(impact_path)
        if row.get("Impact", "").strip()
    }
    invalid: list[tuple[str, str]] = []
    for row in read_tsv(path):
        aid = row.get("Assumption ID", "").strip()
        imp = row.get("Impact", "").strip()
        if imp not in valid:
            invalid.append((aid, imp))

    logger.info("Valid impact levels: %s", sorted(valid))
    assert len(invalid) == 0, f"{len(invalid)} invalid Impact values"
