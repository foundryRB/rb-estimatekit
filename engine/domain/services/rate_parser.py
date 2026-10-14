"""Parsing of resource 'Rate Day' values, shared by every rate consumer."""

from __future__ import annotations

import re

from engine.domain.exceptions.invalid_rate_error import InvalidRateError

__all__ = ["parse_rate_day"]


def parse_rate_day(value: str, *, context: str) -> float:
    """Parse a 'Rate Day' cell ('360', '(EUR) 360', 'EUR 350', '350,5') to a float.

    Currency symbols and codes are stripped and comma decimals honored. An
    empty cell means no rate (0.0). A non-empty cell that still cannot be
    parsed raises InvalidRateError naming the value and *context*, the
    human-readable location of the cell (phase, stream, profile).
    """
    if not value.strip():
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", value.replace(",", "."))
    if cleaned:
        try:
            return float(cleaned)
        except ValueError:
            raise InvalidRateError(value, context) from None
    raise InvalidRateError(value, context)
