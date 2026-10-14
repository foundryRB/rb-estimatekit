"""A project rename was requested without any target to rename to."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class InvalidRenameError(AppError):
    """A project rename was requested without any target to rename to."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(
            f"Rename of '{slug}' needs a new_slug, a new_name, or both"
        )
