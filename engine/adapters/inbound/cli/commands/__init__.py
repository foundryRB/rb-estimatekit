"""CLI command definitions — Arg, CommandSpec, and the command registry."""

from engine.adapters.inbound.cli.commands.arg import Arg
from engine.adapters.inbound.cli.commands.command_spec import CommandSpec
from engine.adapters.inbound.cli.commands.registry import COMMANDS

__all__ = ["COMMANDS", "Arg", "CommandSpec"]
