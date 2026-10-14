"""Outbound adapter: build Slidev decks using a shared toolchain.

Implements :class:`~engine.application.ports.outbound.slides_builder.SlidesBuilder`
by calling the Slidev CLI from a **shared** ``modern/slidev/`` directory that
has ``@slidev/cli`` pre-installed.  No per-project ``npm install`` is needed.

A directory junction links each project's ``slides/node_modules`` to the
shared toolchain's ``node_modules`` so that Slidev resolves themes, icons,
and plugins without copying or installing anything per project.

All calls are **synchronous** (plain ``subprocess.run``) because the caller
(:class:`~engine.application.use_cases.generate_all.GenerateAll`)
already runs inside a thread executor.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from engine.logging import get_logger

logger = get_logger(__name__)

# Default toolchain: <workspace>/slidev/  (sibling of engine/)
_DEFAULT_TOOLCHAIN = Path(__file__).resolve().parents[4] / "slidev"


class SlidevBuilder:
    """Build Slidev decks using a shared, pre-installed CLI toolchain."""

    def __init__(self, toolchain_dir: Path | None = None) -> None:
        self._toolchain_dir = (toolchain_dir or _DEFAULT_TOOLCHAIN).resolve()
        self._node_modules = self._toolchain_dir / "node_modules"

    def build(self, slides_dir: Path, *, base_path: str = "/") -> bool:
        """Compile the Slidev project synchronously.

        Args:
            slides_dir: Directory containing ``slides.md`` + ``pages/``.
            base_path:  URL base path for the built HTML site.

        Returns:
            True if the build succeeded, False otherwise.
        """
        entry = slides_dir / "slides.md"
        if not entry.is_file():
            logger.warning("No slides.md in %s — skipping Slidev build", slides_dir)
            return False

        cmd = self._build_command(entry, slides_dir / "dist", base_path)
        if cmd is None:
            return False

        self._ensure_node_modules_link(slides_dir)

        dist = slides_dir / "dist"
        logger.info("Building Slidev deck in %s …", slides_dir)

        if not self._run(cmd, cwd=slides_dir):
            return False

        if dist.is_dir():
            logger.info("✓ Slidev build complete (%d files)", len(list(dist.rglob("*"))))
            return True

        logger.warning("Slidev build produced no dist/ directory")
        return False

    def _ensure_node_modules_link(self, slides_dir: Path) -> None:
        """Create a directory junction from slides_dir/node_modules to the shared toolchain."""
        link = slides_dir / "node_modules"
        if link.is_dir():
            if link.is_symlink() or _is_junction(link):
                return  # already linked
            # Real node_modules dir from old approach — remove it
            shutil.rmtree(link, ignore_errors=True)

        if os.name == "nt":
            # mklink /J doesn't require admin on Windows
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(self._node_modules)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            link.symlink_to(self._node_modules)
        logger.debug("Linked %s → %s", link, self._node_modules)

    def _build_command(
        self, entry: Path, out_dir: Path, base_path: str,
    ) -> list[str] | None:
        """Construct the CLI command to build the slides."""
        cli = self._find_cli()
        if cli is None:
            return None
        return [*cli, "build", str(entry), "--out", str(out_dir), "--base", base_path]

    def _find_cli(self) -> list[str] | None:
        """Locate the Slidev CLI binary. Returns the command prefix or None."""
        bin_dir = self._node_modules / ".bin"

        for name in ("slidev.cmd", "slidev"):
            cli = bin_dir / name
            if cli.is_file():
                return [str(cli)]

        mjs = self._node_modules / "@slidev" / "cli" / "bin" / "slidev.mjs"
        node = shutil.which("node")
        if mjs.is_file() and node:
            return [node, str(mjs)]

        logger.warning(
            "Slidev CLI not found in %s — run 'npm install' in that directory",
            self._toolchain_dir,
        )
        return None

    def _run(self, cmd: list[str], *, cwd: Path, timeout: float = 120) -> bool:
        """Run a subprocess with CI=1 to suppress interactive prompts."""
        env = {**os.environ, "CI": "1"}
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                env=env,
                capture_output=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                logger.error(
                    "Command %s failed (rc=%d):\nstdout: %s\nstderr: %s",
                    cmd,
                    result.returncode,
                    result.stdout.decode(errors="replace"),
                    result.stderr.decode(errors="replace"),
                )
                return False
            return True

        except subprocess.TimeoutExpired:
            logger.error("Command %s timed out after %.0fs", cmd, timeout)
            return False


def _is_junction(path: Path) -> bool:
    """Check if a path is a Windows junction point."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))  # type: ignore[union-attr]
        return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
    except Exception:
        return False
