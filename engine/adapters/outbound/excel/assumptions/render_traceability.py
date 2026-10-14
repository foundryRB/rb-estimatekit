"""Render Sheet 3: Traceability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..branding import RB
from .models import TraceabilityData

if TYPE_CHECKING:
    from openpyxl import Workbook


def render_traceability(wb: Workbook, data: TraceabilityData) -> None:
    """Render Sheet 3: Requirement-to-Assumption traceability."""
    ws = wb.create_sheet("Traceability")

    headers = ["Requirement ID", "Count", "Assumption IDs", "Worst Confidence", "Worst Impact"]
    col_widths = {1: 18, 2: 10, 3: 40, 4: 18, 5: 18}
    RB.set_col_widths(ws, col_widths)

    row = RB.apply_title_row(
        ws, 1, len(headers),
        f"{data.project_name} — Requirement ↔ Assumption Traceability",
    )
    row += 1
    row = RB.apply_header_row(ws, row, headers)

    for i, tr in enumerate(data.rows):
        fill = RB.FILL_ALT_ROW if i % 2 == 0 else RB.FILL_WHITE
        vals = [tr.req_id, tr.count, tr.assumption_ids_str, tr.worst_confidence, tr.worst_impact]
        for c, val in enumerate(vals, start=1):
            cell = ws.cell(row=row, column=c, value=val)
            cell.font = RB.FONT_BODY
            cell.fill = fill
            cell.border = RB.BORDER_GRID
            if c == 4:
                cell.font = RB.conf_font(tr.worst_confidence)
                cell.fill = RB.conf_fill(tr.worst_confidence)
            elif c == 5:
                cell.font = RB.impact_font(tr.worst_impact)
                cell.fill = RB.impact_fill(tr.worst_impact)
            cell.alignment = RB.ALIGN_CENTER if c == 2 else RB.ALIGN_LEFT
        row += 1
