"""Declarative description of a single CLI argument."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["Arg"]


@dataclass(frozen=True)
class Arg:
    """Declarative description of a single CLI argument.

    Positional args have a plain *name* (``"root"``).
    Optional/flag args start with ``-`` (``"--force"``).
    All remaining fields map directly to :func:`argparse.ArgumentParser.add_argument`.
    """

    name: str
    help: str = ""
    type: type | None = None
    action: str | None = None
    nargs: str | None = None
    choices: list[Any] | None = None
    default: Any = None

    def add_to(self, parser: Any) -> None:
        """Register this argument on an argparse (sub)parser."""
        kwargs: dict[str, Any] = {}
        if self.help:
            kwargs["help"] = self.help
        if self.type is not None:
            kwargs["type"] = self.type
        if self.action is not None:
            kwargs["action"] = self.action
        if self.nargs is not None:
            kwargs["nargs"] = self.nargs
        if self.choices is not None:
            kwargs["choices"] = self.choices
        if self.default is not None:
            kwargs["default"] = self.default
        parser.add_argument(self.name, **kwargs)
