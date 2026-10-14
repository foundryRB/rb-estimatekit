"""Activity check helpers — shared computation functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from auditor.tsv import read_tsv

__all__ = [
    "DAYS_PER_MONTH",
    "month_columns",
    "overloaded_month_cells",
    "parse_md",
    "read_config",
    "resource_grand_total",
    "resource_total_by_stream",
    "stream_effort",
]

DAYS_PER_MONTH: int = 20


def month_columns(rows: list[dict[str, str]]) -> list[str]:
    """Extract month column names from resource rows (columns after 'Rate Day')."""
    if not rows:
        return []
    keys = list(rows[0].keys())
    idx = keys.index("Rate Day")
    return keys[idx + 1 :]


def parse_md(val: str | None) -> float:
    """Parse a man-day value (effort or capacity, possibly fractional), 0.0 on empty."""
    val = val.strip() if val else ""
    return float(val) if val else 0.0


def resource_total_by_stream(rows: list[dict[str, str]], stream_prefix: str) -> float:
    """Sum resource capacity for rows matching a stream prefix."""
    cols = month_columns(rows)
    return sum(
        parse_md(row.get(m, ""))
        for row in rows
        if row.get("Stream", "").startswith(stream_prefix)
        for m in cols
    )


def resource_grand_total(rows: list[dict[str, str]]) -> float:
    """Sum total resource capacity across all rows and months."""
    cols = month_columns(rows)
    return sum(parse_md(row.get(m, "")) for row in rows for m in cols)


def overloaded_month_cells(
    rows: list[dict[str, str]],
) -> list[tuple[str, str, str, float]]:
    """Resource month cells booked above DAYS_PER_MONTH (physically impossible).

    Each resource row is one staffing line, and a month cell is that line's
    man-days in that month. The scheduling model fixes a month at DAYS_PER_MONTH
    working days, so a single line cannot deliver more than that in one month; a
    larger value is a data error (it silently inflates stream capacity), not a
    planning choice. Returns ``(stream, profile, month, value)`` per offending
    cell, in row-then-month order.
    """
    cols = month_columns(rows)
    return [
        (row.get("Stream", "").strip(), row.get("Profile", "").strip(), m, value)
        for row in rows
        for m in cols
        if (value := parse_md(row.get(m, ""))) > DAYS_PER_MONTH
    ]


def stream_effort(project_rows: list[dict[str, str]], stream_prefix: str) -> float:
    """Sum Effort (MD) for rows matching a stream prefix."""
    total = 0.0
    for row in project_rows:
        if row.get("Stream", "").strip().startswith(stream_prefix):
            total += parse_md(row.get("Effort (MD)", ""))
    return total


def read_config(config_path: Path) -> dict[str, Any]:
    """Read phase config TSV and return design/lag/SIT/UAT parameters."""
    defaults: dict[str, Any] = {
        "design_lead_days": 0.0,
        "lag_pct": 0.0,
        "sit_days": 0.0,
        "uat_days": 0.0,
    }
    if not config_path.exists():
        return defaults
    rows = read_tsv(config_path)
    param_map = {
        "Design Lead": "design_lead_days",
        "Testing Lag": "lag_pct",
        "SIT Duration": "sit_days",
        "UAT Duration": "uat_days",
    }
    result = dict(defaults)
    for row in rows:
        param = row.get("Parameter", "").strip()
        value = row.get("Value", "0").strip()
        key = param_map.get(param)
        if key:
            result[key] = float(value) if value else 0.0
    return result
