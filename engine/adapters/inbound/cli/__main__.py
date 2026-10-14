"""CLI entry point — ``python -m engine.adapters.inbound.cli <command>``."""

from __future__ import annotations

import logging
import sys

from engine.adapters.inbound.cli.utils.parser import build_parser
from engine.adapters.inbound.cli.utils.runner import run
from engine.logging import configure_logging, get_logger

logger = get_logger(__name__)


def dispatch(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and dispatch to the correct use case.

    Returns an exit code (0 = success).
    """
    configure_logging()

    parser, command_map = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        configure_logging(level=logging.DEBUG)

    spec = command_map.get(args.command)
    if spec is None:
        logger.error("Unknown command: %s", args.command)
        return 1

    return run(spec, args)


def main() -> None:
    """Entry point for the CLI adapter."""
    exit_code = dispatch(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
