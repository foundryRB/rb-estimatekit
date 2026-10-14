"""Render Sheet 2: Risk Matrix."""

from __future__ import annotations

from typing import TYPE_CHECKING

from openpyxl.styles import Font, PatternFill

from ..branding import CF
from .models import CONF_ORDER, IMPACT_ORDER, RiskMatrixData

if TYPE_CHECKING:
    from openpyxl import Workbook


def render_risk_matrix(wb: Workbook, data: RiskMatrixData) -> None:
    """Render Sheet 2: Risk Matrix (confidence × impact heat-map)."""
    ws = wb.create_sheet("Risk Matrix")

    if data.total == 0:
        return

    col_widths = {1: 16}
    for i in range(len(IMPACT_ORDER)):
        col_widths[i + 2] = 16
    col_widths[len(IMPACT_ORDER) + 2] = 14  # total column
    CF.set_col_widths(ws, col_widths)

    row = CF.apply_title_row(
        ws, 1, len(IMPACT_ORDER) + 2,
        f"{data.project_name} — Risk Matrix",
        "Confidence × Impact heat-map",
    )
    row += 1

    # Header: blank, then impact columns, then Total
    headers = ["Confidence \\ Impact"] + IMPACT_ORDER + ["Total"]
    row = CF.apply_header_row(ws, row, headers)

    # Grid rows — one per confidence level
    for conf in CONF_ORDER:
        cell = ws.cell(row=row, column=1, value=conf)
        cell.font = CF.conf_font(conf)
        cell.fill = CF.conf_fill(conf)
        cell.border = CF.BORDER_GRID
        cell.alignment = CF.ALIGN_CENTER

        row_total = 0
        for ci, imp in enumerate(IMPACT_ORDER):
            cnt = data.matrix.get((conf, imp), 0)
            row_total += cnt
            pct = cnt / data.total if data.total else 0
            label = f"{cnt}  ({pct:.0%})" if cnt else ""
            cell = ws.cell(row=row, column=ci + 2, value=label)
            cell.fill = CF.heat_fill(conf, imp)
            cell.font = CF.heat_font(conf, imp)
            cell.border = CF.BORDER_GRID
            cell.alignment = CF.ALIGN_CENTER

        # Row total
        cell = ws.cell(row=row, column=len(IMPACT_ORDER) + 2, value=row_total)
        cell.font = CF.FONT_BODY_BOLD
        cell.fill = CF.FILL_CARD
        cell.border = CF.BORDER_GRID
        cell.alignment = CF.ALIGN_CENTER
        row += 1

    # Per-impact totals row
    cell = ws.cell(row=row, column=1, value="Total")
    cell.font = CF.FONT_BODY_BOLD
    cell.fill = CF.FILL_CARD
    cell.border = CF.BORDER_GRID
    cell.alignment = CF.ALIGN_CENTER
    for ci, imp in enumerate(IMPACT_ORDER):
        col_total = sum(data.matrix.get((c, imp), 0) for c in CONF_ORDER)
        cell = ws.cell(row=row, column=ci + 2, value=col_total)
        cell.font = CF.FONT_BODY_BOLD
        cell.fill = CF.FILL_CARD
        cell.border = CF.BORDER_GRID
        cell.alignment = CF.ALIGN_CENTER
    cell = ws.cell(row=row, column=len(IMPACT_ORDER) + 2, value=data.total)
    cell.font = CF.FONT_TOTAL
    cell.fill = CF.FILL_TOTAL
    cell.border = CF.BORDER_GRID
    cell.alignment = CF.ALIGN_CENTER
    row += 2

    # Key risks callout (LOW confidence + CRITICAL/HIGH impact)
    if data.key_risks:
        ws.merge_cells(
            start_row=row, start_column=1,
            end_row=row, end_column=len(IMPACT_ORDER) + 2,
        )
        risk_msg = (
            f"Key Risks — {len(data.key_risks)} assumptions"
            f" with LOW confidence and CRITICAL/HIGH impact"
        )
        cell = ws.cell(row=row, column=1, value=risk_msg)
        cell.font = Font(name=CF.FONT_FAMILY, size=11, bold=True, color="C62828")
        cell.fill = PatternFill("solid", fgColor="FCE4EC")
        cell.alignment = CF.ALIGN_LEFT
        row += 1
        for kr in data.key_risks:
            ws.merge_cells(
                start_row=row, start_column=1,
                end_row=row, end_column=len(IMPACT_ORDER) + 2,
            )
            cell = ws.cell(row=row, column=1,
                           value=f"  {kr.assumption_id}: {kr.short_title} [{kr.impact}]")
            cell.font = CF.FONT_BODY
            cell.alignment = CF.ALIGN_LEFT
            row += 1
