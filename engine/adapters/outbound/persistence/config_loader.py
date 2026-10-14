"""Loader: project configuration from YAML."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.persistence.yaml_io import read_yaml, write_yaml
from engine.domain.model.value_objects.branding import BrandConfig
from engine.domain.model.value_objects.config import ProjectConfig

__all__ = ["load_config", "save_config_data"]


def load_config(project_path: Path) -> ProjectConfig:
    """Load project.yaml → ProjectConfig."""
    raw = read_yaml(project_path / "project.yaml")
    branding_raw = raw.get("branding", {})
    # Defaults must match BrandConfig dataclass defaults
    _brand_defaults = BrandConfig()
    return ProjectConfig(
        name=raw.get("name", ""),
        short_name=raw.get("short_name", ""),
        client=raw.get("client", ""),
        author=raw.get("author", ""),
        description=raw.get("description", ""),
        date=raw.get("date", ""),
        branding=BrandConfig(
            primary_color=branding_raw.get("primary_color", _brand_defaults.primary_color),
            company=branding_raw.get("company", _brand_defaults.company),
            font_url=branding_raw.get("font_url", _brand_defaults.font_url),
            font_family=branding_raw.get("font_family", _brand_defaults.font_family),
        ),
        features=raw.get("features", {}),
    )


def save_config_data(project_path: Path, config: ProjectConfig) -> None:
    """Persist the project config to project.yaml."""
    data: dict = {
        "name": config.name,
        "short_name": config.short_name,
        "client": config.client,
        "author": config.author,
        "description": config.description,
        "date": config.date,
        "branding": {
            "primary_color": config.branding.primary_color,
            "company": config.branding.company,
            "font_url": config.branding.font_url,
            "font_family": config.branding.font_family,
        },
    }
    if config.features:
        data["features"] = config.features
    write_yaml(project_path / "project.yaml", data)
