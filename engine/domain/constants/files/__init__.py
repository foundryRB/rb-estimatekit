"""File naming conventions and helper functions for TSV/Excel I/O.

Sub-modules:
  - ``inputs``    — source / input TSV file constants and helpers
  - ``outputs``   — generated Excel workbook constants and helpers
  - ``templates`` — Excel template file constants
  - ``roadmaps``  — roadmap output file helpers
  - ``markers``   — project lifecycle marker filenames
"""

from engine.domain.constants.files.inputs import (
    FILE_ASSUMPTIONS,
    FILE_BRD,
    FILE_CONFIDENCE,
    FILE_CUSTOMER_REQUIREMENTS,
    FILE_GUIDELINES,
    FILE_IMPACT,
    FILE_MATRIX,
    FILE_PHASES,
    SLIDES_EXECUTIVE_SUMMARY,
    SLIDES_NOTES,
    architecture_file,
    phase_file,
    slides_file,
    slides_path,
)
from engine.domain.constants.files.markers import ARCHIVED_MARKER
from engine.domain.constants.files.outputs import (
    OUT_ASSUMPTIONS_XLSX,
    OUT_GUIDELINES_XLSX,
    OUT_REQUIREMENTS_XLSX,
    out_estimation_xlsx,
    out_financial_xlsx,
    out_quoter_xlsx,
)
from engine.domain.constants.files.roadmaps import roadmap_file
from engine.domain.constants.files.templates import TEMPLATE_FINANCIAL, TEMPLATE_QUOTER

__all__ = [
    # inputs
    "FILE_ASSUMPTIONS",
    "FILE_BRD",
    "FILE_CONFIDENCE",
    "FILE_CUSTOMER_REQUIREMENTS",
    "FILE_GUIDELINES",
    "FILE_IMPACT",
    "FILE_MATRIX",
    "FILE_PHASES",
    "SLIDES_EXECUTIVE_SUMMARY",
    "SLIDES_NOTES",
    "architecture_file",
    "phase_file",
    "slides_file",
    "slides_path",
    # outputs
    "OUT_ASSUMPTIONS_XLSX",
    "OUT_GUIDELINES_XLSX",
    "OUT_REQUIREMENTS_XLSX",
    "out_estimation_xlsx",
    "out_financial_xlsx",
    "out_quoter_xlsx",
    # markers
    "ARCHIVED_MARKER",
    # roadmaps
    "roadmap_file",
    # templates
    "TEMPLATE_FINANCIAL",
    "TEMPLATE_QUOTER",
]
