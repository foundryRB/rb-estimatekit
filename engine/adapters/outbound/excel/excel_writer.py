"""Excel writer — implements ExcelWriter port.

Orchestrates all individual Excel workbook generators and writes
them to the output directory.
"""

from __future__ import annotations

from pathlib import Path

from engine.domain.exceptions import GenerationError, TemplateNotFoundError
from engine.domain.model.aggregates.project import Project
from engine.logging import get_logger

from . import assumptions, estimations, financial, guidelines, quoter, requirements

logger = get_logger(__name__)


class OpenpyxlExcelWriter:
    """Generate Excel workbooks from the Project domain model."""

    def write_all(self, project: Project, output_dir: Path) -> int:
        """Write all Excel workbooks to the output directory.

        Returns the number of workbooks written.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Generating Excel deliverables")

        count = 0
        generators: list[tuple[str, ...]] = [
            ("requirements", requirements),
            ("estimations", estimations),
            ("quoter", quoter),
            ("financial", financial),
            ("assumptions", assumptions),
            ("guidelines", guidelines),
        ]

        for name, module in generators:
            try:
                n = module.generate(project, output_dir)
                count += n
                if n > 0:
                    logger.info("  %s: %d file(s)", name, n)
            except TemplateNotFoundError as exc:
                logger.warning("  %s: skipped — %s", name, exc)
            except GenerationError:
                raise
            except Exception as exc:
                raise GenerationError(name, str(exc)) from exc

        logger.info("%d Excel file(s) generated", count)
        return count
