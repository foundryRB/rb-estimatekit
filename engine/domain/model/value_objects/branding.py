"""BrandConfig — visual identity for project branding."""

from __future__ import annotations

from dataclasses import dataclass

from engine.domain.constants.colors import DEFAULT_PRIMARY_CSS

__all__ = ["BrandConfig"]


@dataclass(frozen=True)
class BrandConfig:
    """Visual identity — colors, fonts, company branding."""

    primary_color: str = DEFAULT_PRIMARY_CSS
    company: str = "RB"
    font_url: str = ""
    font_family: str = "Aptos"
