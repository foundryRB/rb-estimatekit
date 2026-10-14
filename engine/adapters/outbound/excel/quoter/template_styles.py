"""Template row snapshot and style application helpers."""

from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openpyxl.worksheet.worksheet import Worksheet

# Template column layout (1-indexed, fixed):
#  A=1  Stream          B=2  Name         C=3  Profile
#  D=4  Rate Day        E=5  Rate Hour (=D/8)
#  F=6..K=11  Month days (6 cols)         L=12  Total FTE (=SUM(F:K))
#  M=13..R=18  Month costs (=$D*F .. =$D*K)  S=19  Total Cost (=SUM(M:R))
#  T=20  GM% Target (=$T$5)  U=21  % Cost Real (1)
#  V=22  Total Cost Real (=S*U)  W=23  Total Revenue (=S/(1-T))
MAX_COL = 25


def snapshot_row(
    ws: Worksheet, row: int,
) -> tuple[dict[int, dict], float | None]:
    """Save cell styles and row height for a template row."""
    styles: dict[int, dict] = {}
    for col in range(1, MAX_COL + 1):
        cell = ws.cell(row=row, column=col)
        styles[col] = {
            "font": copy(cell.font),
            "fill": copy(cell.fill),
            "border": copy(cell.border),
            "number_format": cell.number_format,
            "alignment": copy(cell.alignment),
        }
    height = ws.row_dimensions[row].height
    return styles, height


def apply_styles(
    ws: Worksheet, row: int, styles: dict[int, dict], height: float | None,
) -> None:
    """Apply saved styles to every cell in a row."""
    for col, s in styles.items():
        cell = ws.cell(row=row, column=col)
        cell.font = s["font"]
        cell.fill = s["fill"]
        cell.border = s["border"]
        cell.number_format = s["number_format"]
        cell.alignment = s["alignment"]
    if height is not None:
        ws.row_dimensions[row].height = height
