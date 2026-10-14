"""The rows a phase brings with it when it is minted.

Minting a phase appends its row to the phase table, example-marked so the
audit refuses it until authored, and inserts an empty column into the
requirements matrix before Notes, where the author marks the requirements
the phase carries.
"""

from __future__ import annotations

import re

from engine.domain.constants.columns import (
    COL_DESCRIPTION,
    COL_EXAMPLES,
    COL_INTEGRATION_TYPE,
    COL_NAME,
    COL_PHASE,
    COL_PHASE_ID,
)

__all__ = [
    "EXAMPLE_SENTINEL",
    "PHASE_ID_PATTERN",
    "phase_display_name",
    "phase_table_row",
]

EXAMPLE_SENTINEL = "[EXAMPLE]"
"""The scaffold sentinel the audit refuses until the value is authored."""

PHASE_ID_PATTERN = re.compile(r"^P\d+$")
"""The ``P<n>`` form that names a phase's files."""


def phase_display_name(phase_id: str) -> str:
    """The display name of phase *phase_id*: the matrix column header (``Phase 3``)."""
    return f"Phase {phase_id[1:]}"


def phase_table_row(header: list[str], phase_id: str) -> list[str]:
    """The example-marked phase-table row for *phase_id*, ordered by *header*."""
    number = phase_id[1:]
    values = {
        COL_PHASE: phase_display_name(phase_id),
        COL_PHASE_ID: phase_id,
        COL_NAME: f"{EXAMPLE_SENTINEL} Phase {number} Name",
        COL_DESCRIPTION: f"{EXAMPLE_SENTINEL} What phase {number} delivers, in one sentence",
        COL_INTEGRATION_TYPE: f"{EXAMPLE_SENTINEL} Integration type",
        COL_EXAMPLES: f"{EXAMPLE_SENTINEL} One example capability, Another example capability",
    }
    return [values.get(column, "") for column in header]
