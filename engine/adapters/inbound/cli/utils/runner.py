"""CLI command runner — resolves the use case and invokes it."""

from __future__ import annotations

import argparse

from engine.adapters.inbound.cli.commands import CommandSpec
from engine.adapters.inbound.cli.mappers.exception_mapper import DEFAULT_EXIT_CODE, EXIT_CODE_MAP
from engine.container import Container
from engine.domain.exceptions import AppError
from engine.logging import get_logger

logger = get_logger(__name__)


def run(spec: CommandSpec, args: argparse.Namespace) -> int:
    """Resolve the use case, call ``execute()``, format output."""
    container = Container()
    port = getattr(container, spec.container_method)()

    kwargs = {
        port_kwarg: getattr(args, cli_attr)
        for cli_attr, port_kwarg in spec.execute_args.items()
        if hasattr(args, cli_attr)
    }

    try:
        result = port.execute(**kwargs)
    except AppError as exc:
        logger.error("%s: %s", type(exc).__name__, exc)
        return EXIT_CODE_MAP.get(type(exc), DEFAULT_EXIT_CODE)

    if spec.mapper is not None:
        result = spec.mapper(result)

    if spec.formatter is not None:
        return spec.formatter(result)

    return 0
