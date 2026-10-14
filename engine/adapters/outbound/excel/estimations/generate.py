"""Entry point for estimation workbook generation."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from engine.domain.model.aggregates.project import Project
from engine.logging import get_logger

from .prepare import prepare_estimation
from .render_build import render_build
from .render_estimate import render_estimate

logger = get_logger(__name__)

__all__ = ["generate"]


def generate(project: Project, output_dir: Path, *, templates_dir: Path | None = None) -> int:
    """Generate one estimation workbook per phase. Returns files written."""
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for phase in project.phases:
        effort = phase.compute_effort()
        data = prepare_estimation(phase, effort)

        wb = Workbook()
        render_build(wb, data)
        render_estimate(wb, data)

        fname = f"{phase.phase_id}_Estimation.xlsx"
        wb.save(output_dir / fname)
        logger.info("Wrote %s", fname)
        count += 1
    return count
