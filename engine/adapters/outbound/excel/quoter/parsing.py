"""Discovery utilities for quoter data."""

from __future__ import annotations


def discover_month_keys(rows: list[dict[str, str]], max_months: int = 6) -> list[str]:
    """Find month column keys (M1, M2 …) present in the resource rows."""
    if not rows:
        return [f"M{i}" for i in range(1, max_months + 1)]
    keys = [k for k in rows[0] if k.startswith("M") and k[1:].isdigit()]
    keys.sort(key=lambda k: int(k[1:]))
    return keys[:max_months]
