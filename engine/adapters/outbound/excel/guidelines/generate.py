"""Entry point for Architecture Guidelines workbook generation."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from engine.domain.model.aggregates.project import Project
from engine.logging import get_logger

from .prepare import prepare_guidelines
from .render_overview import render_overview
from .render_summary import render_summary

logger = get_logger(__name__)

__all__ = ["generate"]


def generate(project: Project, output_dir: Path, *, templates_dir: Path | None = None) -> int:
    """Generate the Architecture Guidelines workbook. Returns files written."""
    output_dir.mkdir(parents=True, exist_ok=True)

    data = prepare_guidelines(project)
    if data is None:
        logger.warning("No guidelines to write.")
        return 0

    wb = Workbook()
    render_overview(wb, data)
    render_summary(wb, data)

    fname = "Architecture_Guidelines.xlsx"
    wb.save(output_dir / fname)
    logger.info("Wrote %s", fname)
    return 1
