"""Man-days: the unit every effort figure is quoted in, and its text form."""

from __future__ import annotations

__all__ = ["MAX_MD_DECIMALS", "format_md"]

# Effort is authored in whole and half days, and a rate-driven figure can carry
# a second decimal; past that the precision is float noise, not estimate.
MAX_MD_DECIMALS = 2


def format_md(value: float) -> str:
    """Render a man-day figure at the precision it carries.

    A whole number of days renders whole and a fractional one keeps its
    decimal, so every figure on a surface is the figure itself rather than a
    rounded stand-in. That is what lets a table add up: rounding each part to a
    whole day and leaving the total unrounded is exactly how a column of 30s
    comes to sit under a total of 91, and a reader who checks the arithmetic
    finds the deck wrong about its own numbers.

    Nothing here rounds toward a display width. The caller sums the real values
    and formats the result, so a total is the sum of the parts beside it for
    any data authored to ``MAX_MD_DECIMALS`` or fewer, which is all of it.
    """
    rounded = round(value, MAX_MD_DECIMALS)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.{MAX_MD_DECIMALS}f}".rstrip("0")
