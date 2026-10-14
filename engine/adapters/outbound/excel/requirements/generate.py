"""Entry point for requirements workbook generation."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from engine.domain.model.aggregates.project import Project
from engine.logging import get_logger

from .prepare import prepare_requirements
from .render_category_summary import render_category_summary
from .render_requirements import render_requirements
from .render_summary import render_summary

logger = get_logger(__name__)

__all__ = ["generate"]


def generate(project: Project, output_dir: Path, *, templates_dir: Path | None = None) -> int:
    """Generate Customer Requirements Matrix workbook.

    Returns the number of workbooks written (0 or 1).
    """
    data = prepare_requirements(project)
    if data is None:
        logger.warning("No requirements data — skipping Requirements Matrix")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    render_summary(wb, data)
    render_requirements(wb, data)
    render_category_summary(wb, data)

    filepath = output_dir / "Customer_Requirements_Matrix.xlsx"
    wb.save(filepath)
    logger.info("✓ %s", filepath.name)
    return 1
