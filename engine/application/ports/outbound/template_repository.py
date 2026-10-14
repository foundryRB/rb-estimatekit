"""Port: template repository — access to scaffolding templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class TemplateRepository(Protocol):
    """Access and deploy project scaffolding templates."""

    def list_templates(self) -> list[str]:
        """Return names of all available template files."""
        ...

    def scaffold_to(self, target_dir: Path, *, force: bool = False) -> int:
        """Copy all templates into the target directory.

        Returns the number of files written.
        Skips existing files unless force=True.
        """
        ...

    def scaffold_phase_to(
        self, target_dir: Path, phase_id: str, *, force: bool = False,
    ) -> list[str]:
        """Copy the template phase's file set into the target directory as *phase_id*.

        Returns the relative paths written (under the target directory).
        Skips existing files unless force=True.
        """
        ...

    def read_guide(self) -> dict[str, Any]:
        """Read and return the parsed guide content."""
        ...

    def read_project_template(self) -> str | None:
        """Return the raw text of project.yaml template, or None."""
        ...
