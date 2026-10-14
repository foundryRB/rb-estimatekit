"""Port: slides builder — compile slide markdown into static HTML."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class SlidesBuilder(Protocol):
    """Build a Slidev project into a static HTML site.

    Implementations use a shared Slidev CLI toolchain to compile
    the generated markdown into a static HTML site.
    """

    def build(self, slides_dir: Path, *, base_path: str = "/") -> bool:
        """Compile the Slidev project.

        Args:
            slides_dir: Directory containing ``slides.md`` + ``pages/``.
            base_path:  URL base path for the built HTML site
                        (e.g. ``/projects/my-proj/slides/``).

        Returns:
            True if the build succeeded, False otherwise.
        """
        ...
