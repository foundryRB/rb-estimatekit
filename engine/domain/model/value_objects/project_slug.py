"""ProjectSlug — validated, immutable identifier for a project."""

from __future__ import annotations

import re
from typing import Final

from engine.domain.exceptions import InvalidSlugError

__all__ = ["ProjectSlug"]

_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


class ProjectSlug:
    """A validated project slug — alphanumeric, dashes, underscores only.

    Raises :class:`InvalidSlugError` at construction time if the raw
    value does not match the allowed pattern.
    """

    __slots__ = ("_value",)

    def __init__(self, raw: str) -> None:
        if not _SLUG_RE.fullmatch(raw):
            raise InvalidSlugError(raw)
        self._value = raw

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"ProjectSlug({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ProjectSlug):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)
