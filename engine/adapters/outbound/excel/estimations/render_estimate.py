"""Render Sheet 2: Project Estimate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..branding import RB
from .models import EstimationData

if TYPE_CHECKING:
    from openpyxl import Workbook


def render_estimate(wb: Workbook, data: EstimationData) -> None:
    """Render Sheet 2: Project Estimate."""
    ws = wb.create_sheet("Project Estimate")

    headers = ["Category", "Effort (MD)", "% of Total"]
    col_widths = {1: 40, 2: 16, 3: 16}
    RB.set_col_widths(ws, col_widths)

    row = RB.apply_title_row(ws, 1, len(headers), f"{data.phase_name} — Delivery Estimate")
    row += 1  # spacer

    row = RB.apply_header_row(ws, row, headers)

    phase_fill = RB.phase_fill(data.phase_id)
    # Percentages read against the total of the rows above them, so they sum to 100%.
    grand = data.authored_total if data.authored_total else 1.0

    for i, er in enumerate(data.estimate_rows):
        fill = RB.FILL_ALT_ROW if i % 2 == 0 else RB.FILL_WHITE
        font = RB.FONT_BODY_BOLD if er.is_header else RB.FONT_BODY
        pct = er.effort_md / grand

        ws.cell(row=row, column=1, value=er.label).font = font
        ws.cell(row=row, column=1).fill = fill
        ws.cell(row=row, column=1).alignment = RB.ALIGN_LEFT
        ws.cell(row=row, column=1).border = RB.BORDER_GRID

        cell = ws.cell(row=row, column=2, value=er.effort_md)
        cell.font = font
        cell.fill = fill
        cell.alignment = RB.ALIGN_RIGHT
        cell.border = RB.BORDER_GRID

        cell = ws.cell(row=row, column=3, value=f"{pct:.0%}")
        cell.font = font
        cell.fill = fill
        cell.alignment = RB.ALIGN_RIGHT
        cell.border = RB.BORDER_GRID

        row += 1

    # PHASE TOTAL
    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=1)
    cell = ws.cell(row=row, column=1, value="PHASE TOTAL")
    cell.font = RB.FONT_TOTAL
    cell.fill = phase_fill
    cell.alignment = RB.ALIGN_LEFT
    cell.border = RB.BORDER_GRID

    cell = ws.cell(row=row, column=2, value=data.authored_total)
    cell.font = RB.FONT_TOTAL
    cell.fill = phase_fill
    cell.alignment = RB.ALIGN_RIGHT
    cell.border = RB.BORDER_GRID

    cell = ws.cell(row=row, column=3, value="100%")
    cell.font = RB.FONT_TOTAL
    cell.fill = phase_fill
    cell.alignment = RB.ALIGN_RIGHT
    cell.border = RB.BORDER_GRID

    ws.row_dimensions[row].height = 26

    # Staffed capacity: a different quantity from the estimate above, so it sits
    # below the total under its own label rather than standing in for it.
    row += 1
    cell = ws.cell(row=row, column=1, value="Staffed capacity (resource plan)")
    cell.font = RB.FONT_BODY
    cell.alignment = RB.ALIGN_LEFT
    cell = ws.cell(row=row, column=2, value=data.staffed_capacity)
    cell.font = RB.FONT_BODY
    cell.alignment = RB.ALIGN_RIGHT
