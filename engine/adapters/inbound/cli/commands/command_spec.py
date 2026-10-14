"""Declarative description of a single CLI command."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.adapters.inbound.cli.commands.arg import Arg

__all__ = ["CommandSpec"]


@dataclass(frozen=True)
class CommandSpec:
    """Declarative description of a single CLI command.

    *container_method*: name of the :class:`Container` factory method
    that returns the inbound port (e.g. ``"discover_projects"``).

    *execute_args*: maps ``argparse`` attribute names to the keyword
    argument names expected by the port's ``execute()`` method.
    For example ``{"root": "projects_root"}`` means
    ``port.execute(projects_root=args.root)``.

    *mapper*: optional callable ``(domain_result) -> mapped`` to
    translate the domain object into a CLI-layer representation
    before formatting.

    *formatter*: optional callable ``(result) -> int`` to present the
    (mapped) result and return an exit code. Defaults to a no-op
    ``return 0``.
    """

    name: str
    help: str
    container_method: str
    args: list[Arg] = field(default_factory=list)
    execute_args: dict[str, str] = field(default_factory=dict)
    mapper: Any = None  # Callable[[Any], Any] | None
    formatter: Any = None  # Callable[[Any], int] | None
