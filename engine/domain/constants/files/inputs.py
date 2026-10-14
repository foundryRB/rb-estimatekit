"""Source / input file naming conventions.

Constants for the TSV files the system reads from a project directory,
plus helpers that build phase-qualified input filenames.

Data files live under ``data/`` in semantic subdirectories::

    data/
    ├── requirements/   — BRD, phases, matrix, customer input
    ├── architecture/   — guidelines, per-phase components & diagrams
    ├── activities/     — per-phase build, config, project, resource
    ├── assumptions/    — confidence & impact scales, assumption register
    └── slides/         — executive summary, speaker notes
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.domain.model.value_objects.phase_id import PhaseId

# ── Subdirectory names ──────────────────────────────────────────────────────

DIR_DATA = "data"
"""The project subfolder that holds every editable data file."""

DIR_REQUIREMENTS = "requirements"
DIR_ARCHITECTURE = "architecture"
DIR_ACTIVITIES = "activities"
DIR_ASSUMPTIONS = "assumptions"
DIR_SLIDES = "slides"

DATA_SUBDIRS: list[str] = [
    DIR_REQUIREMENTS,
    DIR_ARCHITECTURE,
    DIR_ACTIVITIES,
    DIR_ASSUMPTIONS,
    DIR_SLIDES,
]
"""All recognised data subdirectory names (used by scaffold & scan)."""

# ── Filenames (relative to their subdirectory) ─────────────────────────────

# requirements/
FILE_CUSTOMER_REQUIREMENTS = "00-customer-requirements.txt"
FILE_BRD = "01-brd.tsv"
FILE_PHASES = "02-phases.tsv"
FILE_MATRIX = "03-matrix.tsv"

# architecture/
FILE_GUIDELINES = "00-guidelines.tsv"

SUFFIX_DIAGRAM = ".puml"
"""File suffix of the PlantUML architecture diagram sources (in ``architecture/``)."""

ARCHITECTURE_DATA_DIR = f"{DIR_DATA}/{DIR_ARCHITECTURE}"
"""Project-relative path of the architecture folder (diagrams, components, guidelines)."""

# assumptions/
FILE_CONFIDENCE = "00-confidence.tsv"
FILE_IMPACT = "01-impact.tsv"
FILE_ASSUMPTIONS = "02-assumptions.tsv"

# slides/ (per phase: the deck sells one phase, so its pitch copy is the phase's)
SLIDES_EXECUTIVE_SUMMARY = "executive-summary"
"""Kind of a phase's executive-summary file (``P<n>-executive-summary.tsv``)."""
SLIDES_NOTES = "notes"
"""Kind of a phase's speaker-notes file (``P<n>-notes.tsv``)."""


# ── Phase-qualified filename builders ───────────────────────────────────────


def phase_file(phase_id: PhaseId, suffix: str) -> str:
    """Build a phase-qualified activity filename (lives in ``activities/``).

    >>> phase_file("P1", "build")
    'P1-build.tsv'
    """
    return f"{phase_id}-{suffix}.tsv"


def architecture_file(phase_id: PhaseId, kind: str) -> str:
    """Build a phase-qualified architecture filename (lives in ``architecture/``).

    >>> architecture_file("P1", "components")
    'P1-components.tsv'
    """
    return f"{phase_id}-{kind}.tsv"


def slides_file(phase_id: PhaseId, kind: str) -> str:
    """Build a phase-qualified slides filename (lives in ``slides/``).

    >>> slides_file("P1", "executive-summary")
    'P1-executive-summary.tsv'
    """
    return f"{phase_id}-{kind}.tsv"


def slides_path(phase_id: PhaseId, kind: str) -> str:
    """Project-relative path of a phase's slides file.

    >>> slides_path("P1", "executive-summary")
    'data/slides/P1-executive-summary.tsv'
    """
    return f"{DIR_DATA}/{DIR_SLIDES}/{slides_file(phase_id, kind)}"
