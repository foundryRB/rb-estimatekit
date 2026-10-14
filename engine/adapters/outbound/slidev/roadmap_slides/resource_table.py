"""Resource allocation mini-table builder for roadmap slides."""

from __future__ import annotations

from engine.adapters.outbound.slidev.roadmap_slides.colors import hex_to_rgb, phase_color
from engine.adapters.outbound.slidev.roadmap_slides.labels import stream_short
from engine.domain.constants.colors import DEFAULT_PRIMARY_CSS
from engine.domain.model.value_objects.man_days import format_md
from engine.domain.model.value_objects.roadmap_view import RoadmapView

__all__ = ["build_resource_table"]


def build_resource_table(
    view: RoadmapView,
    phase_id: str,
    primary: str = DEFAULT_PRIMARY_CSS,
) -> str:
    """Build a compact resource allocation table (streams x months).

    Uses ``raw_values`` from each :class:`ViewRow` (monthly capacity floats)
    with an opacity heat-map proportional to peak capacity.
    """
    if not view.rows:
        return ""

    color = phase_color(phase_id, primary)
    labels = view.month_labels
    n_months = view.n_months

    # Find peak monthly value across all rows for heat-map scaling
    max_val: float = 1.0
    for row in view.rows:
        if row.raw_values:
            for v in row.raw_values:
                if v > max_val:
                    max_val = v

    html = '\n<div class="rb-resource-wrap" style="margin-top:0.2rem;">\n'
    html += '<table class="rb-resource" style="font-size:0.55rem;">\n<thead>\n'
    html += '<tr class="rb-resource-header">\n'
    html += '  <th class="rb-resource-stream">Stream</th>\n'
    html += '  <th class="rb-resource-total">Total</th>\n'
    for lbl in labels:
        html += f"  <th>{lbl}</th>\n"
    html += "</tr>\n</thead>\n<tbody>\n"

    for row in view.rows:
        stream_display = stream_short(row.label)
        total = row.effort  # effort holds the total for resource rows

        html += "<tr>\n"
        html += f'  <td class="rb-resource-stream">{stream_display}</td>\n'
        html += f'  <td class="rb-resource-total">{format_md(total)}</td>\n'

        for i in range(n_months):
            val = row.raw_values[i] if row.raw_values and i < len(row.raw_values) else 0.0
            # Colour-tinted background proportional to max
            if val > 0 and max_val > 0:
                opacity = min(0.25, 0.08 + (val / max_val) * 0.17)
                rgb = hex_to_rgb(color)
                bg_style = f' style="background:rgba({rgb},{opacity:.2f});"'
            else:
                bg_style = ""
            css_cls = (
                "rb-resource-value-high"
                if val >= max_val * 0.5 and val > 0
                else "rb-resource-value"
            )
            val_display = format_md(val) if val else ""
            html += f'  <td class="{css_cls}"{bg_style}>{val_display}</td>\n'

        html += "</tr>\n"

    html += "</tbody>\n</table>\n</div>"
    return html
