"""Entry point for assumptions register workbook generation."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from engine.domain.model.aggregates.project import Project
from engine.logging import get_logger

from .prepare import prepare_assumptions
from .render_log import render_log
from .render_risk_matrix import render_risk_matrix
from .render_traceability import render_traceability

logger = get_logger(__name__)

__all__ = ["generate"]


def generate(project: Project, output_dir: Path, *, templates_dir: Path | None = None) -> int:
    """Generate the Assumptions Register workbook. Returns files written."""
    output_dir.mkdir(parents=True, exist_ok=True)

    data = prepare_assumptions(project)
    if data is None:
        logger.warning("No assumptions to write.")
        return 0

    wb = Workbook()
    render_log(wb, data.log)
    render_risk_matrix(wb, data.risk_matrix)
    render_traceability(wb, data.traceability)

    fname = "Assumptions_Register.xlsx"
    wb.save(output_dir / fname)
    logger.info("Wrote %s", fname)
    return 1
