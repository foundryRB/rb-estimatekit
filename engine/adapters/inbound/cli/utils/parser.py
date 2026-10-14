"""CLI parser construction from the command registry."""

from __future__ import annotations

import argparse

from engine.adapters.inbound.cli.commands import COMMANDS, CommandSpec


def build_parser() -> tuple[argparse.ArgumentParser, dict[str, CommandSpec]]:
    """Construct the full CLI parser from :data:`COMMANDS`."""
    parser = argparse.ArgumentParser(
        prog="estimatekit",
        description="EstimateKit Engine",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    command_map: dict[str, CommandSpec] = {}
    for spec in COMMANDS:
        sub = subparsers.add_parser(spec.name, help=spec.help)
        for arg in spec.args:
            arg.add_to(sub)
        command_map[spec.name] = spec

    return parser, command_map
