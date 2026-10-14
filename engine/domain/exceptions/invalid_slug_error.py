"""Invalid project slug."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class InvalidSlugError(AppError):
    """The provided project slug is invalid."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Invalid project slug: {slug!r}")
