"""A required template file is missing."""

from __future__ import annotations

from pathlib import Path

from engine.domain.exceptions.app_error import AppError


class TemplateNotFoundError(AppError):
    """A required template file is missing."""

    def __init__(self, template_name: str, search_path: Path) -> None:
        self.template_name = template_name
        self.search_path = search_path
        super().__init__(
            f"Template '{template_name}' not found in {search_path}"
        )
