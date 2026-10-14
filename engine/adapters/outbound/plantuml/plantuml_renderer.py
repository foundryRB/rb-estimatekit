"""Outbound adapter: render PlantUML sources to SVG with a local process.

Implements :class:`~engine.application.ports.outbound.diagram_renderer.DiagramRenderer`
by piping the diagram source through a pinned ``plantuml.jar`` on a headless
JRE (devops/Dockerfile ships both). PlantUML's built-in smetana engine does
the layout, so no graphviz is involved - and the diagram source never leaves
the process boundary: a client's architecture is confidential and must not
round-trip a public rendering server.

All calls are synchronous (plain ``subprocess.run``); the HTTP route runs the
render in a thread executor like the generation pipelines.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from engine.domain.exceptions import DiagramRenderError
from engine.logging import get_logger

__all__ = ["PlantUmlRenderer"]

logger = get_logger(__name__)

# Default jar location: <workspace>/plantuml.jar - /app/plantuml.jar in the
# runtime image (mirrors how SlidevBuilder finds its toolchain).
_DEFAULT_JAR = Path(__file__).resolve().parents[4] / "plantuml.jar"

_RENDER_TIMEOUT_SECONDS = 60.0


class PlantUmlRenderer:
    """Render PlantUML source text to SVG via a local ``plantuml.jar``.

    Implements the :class:`DiagramRenderer` port.
    """

    def __init__(self, jar_path: Path | None = None) -> None:
        self._jar_path = (jar_path or _DEFAULT_JAR).resolve()

    def render_svg(self, source: str) -> str:
        """Return the SVG document for *source*.

        Raises :class:`DiagramRenderError` with the reason when the runtime
        is unavailable, the render fails, or no SVG comes back.
        """
        java = shutil.which("java")
        if java is None:
            raise DiagramRenderError("java runtime not found on PATH")
        if not self._jar_path.is_file():
            raise DiagramRenderError(f"plantuml.jar not found at {self._jar_path}")

        cmd = [
            java,
            "-Djava.awt.headless=true",
            "-jar",
            str(self._jar_path),
            "-tsvg",
            "-pipe",
            "-charset",
            "utf-8",
            "-Playout=smetana",
        ]
        try:
            result = subprocess.run(
                cmd,
                input=source.encode("utf-8"),
                capture_output=True,
                timeout=_RENDER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise DiagramRenderError(
                f"rendering timed out after {_RENDER_TIMEOUT_SECONDS:.0f}s"
            ) from None

        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        if result.returncode != 0 or not stdout.strip():
            reason = stderr or f"plantuml exited with code {result.returncode} and no output"
            logger.warning("PlantUML render failed: %s", reason)
            raise DiagramRenderError(reason)

        start = stdout.find("<svg")
        if start < 0:
            raise DiagramRenderError("plantuml produced no SVG output")
        logger.info("Rendered %d chars of PlantUML source to SVG", len(source))
        return stdout[start:]
