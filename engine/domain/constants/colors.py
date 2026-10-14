"""Phase colour palettes (hex and CSS variants)."""

from __future__ import annotations

DEFAULT_PRIMARY_HEX = "E60000"
"""The brand primary a project gets when its project.yaml sets none (BrandConfig)."""

DEFAULT_PRIMARY_CSS = f"#{DEFAULT_PRIMARY_HEX}"


def phase_colors_hex(primary: str = DEFAULT_PRIMARY_CSS) -> dict[str, str]:
    """The phase palette, bare hex: P1 carries the brand primary colour, the other
    phases their neutral accents. ``primary`` is the project branding.primary_color,
    with or without its ``#``."""
    return {
        "Demo": "1976D2",
        "P1": primary.lstrip("#").upper(),
        "P2": "333333",
        "P3": "999999",
    }


def phase_colors_css(primary: str = DEFAULT_PRIMARY_CSS) -> dict[str, str]:
    """The same palette with the ``#`` prefix, for CSS / HTML / Slidev contexts."""
    return {pid: f"#{h}" for pid, h in phase_colors_hex(primary).items()}


def phase_color_cycle(primary: str = DEFAULT_PRIMARY_CSS) -> list[str]:
    """Ordered cycle for unknown / extra phase IDs."""
    return list(phase_colors_css(primary).values())


PHASE_COLORS_HEX: dict[str, str] = phase_colors_hex()
"""The palette at the default primary, bare hex, for openpyxl fills and other non-CSS contexts."""

PHASE_COLORS_CSS: dict[str, str] = phase_colors_css()
"""The palette at the default primary, ``#``-prefixed."""

PHASE_COLOR_CYCLE: list[str] = phase_color_cycle()
"""Ordered cycle at the default primary."""
