"""Colour palette and conversion helpers for roadmap Gantt slides."""

from __future__ import annotations

__all__ = [
    "DESIGN_COLOR",
    "PHASE_COLOR_CYCLE",
    "PHASE_COLOR_MAP",
    "TEST_COLOR",
    "hex_to_rgb",
    "phase_color",
]

from engine.domain.constants.colors import DEFAULT_PRIMARY_CSS, phase_color_cycle, phase_colors_css

PHASE_COLOR_MAP: dict[str, str] = phase_colors_css()
PHASE_COLOR_CYCLE = phase_color_cycle()

DESIGN_COLOR = "#1976D2"
TEST_COLOR = "#2E7D32"


def phase_color(phase_id: str, primary: str = DEFAULT_PRIMARY_CSS) -> str:
    """Return the accent colour for a phase; P1 carries the brand ``primary``."""
    colors = phase_colors_css(primary)
    if phase_id in colors:
        return colors[phase_id]
    cycle = list(colors.values())
    return cycle[hash(phase_id) % len(cycle)]


def hex_to_rgb(hex_color: str) -> str:
    """Convert ``#RRGGBB`` to ``R,G,B`` for ``rgba()``."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"
    return "0,0,0"
