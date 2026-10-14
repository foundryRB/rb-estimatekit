"""Entry point for Financial Model workbook generation."""

from __future__ import annotations

from pathlib import Path

from engine.domain.constants.files.templates import TEMPLATE_FINANCIAL
from engine.domain.exceptions import TemplateNotFoundError
from engine.domain.model.aggregates.project import Project
from engine.logging import get_logger

from .prepare import prepare_financial
from .render import render_financial

logger = get_logger(__name__)

__all__ = ["generate"]


# Templates live alongside this adapter package
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def generate(
    project: Project,
    output_dir: Path,
    *,
    templates_dir: Path | None = None,
) -> int:
    """Generate Financial Model workbooks for all phases. Returns files written."""
    tpl_dir = templates_dir or _TEMPLATES_DIR
    template_path = tpl_dir / TEMPLATE_FINANCIAL
    if not template_path.exists():
        raise TemplateNotFoundError(TEMPLATE_FINANCIAL, tpl_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for phase in project.phases:
        data = prepare_financial(phase)
        if data is None:
            logger.warning("No capacity data for %s, skipping Financial Model", phase.phase_id)
            continue
        fname = render_financial(template_path, data, output_dir)
        logger.info("Wrote %s (Total SD: %d)", fname, data.total_staff_days)
        count += 1

    return count
