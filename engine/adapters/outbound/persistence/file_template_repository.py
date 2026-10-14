"""File-system template repository — implements TemplateRepository."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import yaml


class FileTemplateRepository:
    """Access and deploy scaffolding templates from the templates/ directory.

    Templates are organised in subdirectories that mirror the project
    ``data/`` layout (``requirements/``, ``architecture/``, etc.).
    """

    _GUIDE_FILENAME = "guide.yaml"
    _PROJECT_FILENAME = "project.yaml"
    _SCAFFOLD_EXCLUDE_DIRS = {"excel"}

    _PHASE_TEMPLATE_ID = "P1"
    """The template phase whose file set a minted phase is copied from."""
    _PHASE_TEMPLATE_TOKEN = re.compile(r"\bP1\b")
    _PHASE_TEMPLATE_NAME = "Phase 1"

    def __init__(self, templates_dir: Path) -> None:
        self._dir = templates_dir

    def list_templates(self) -> list[str]:
        """Return relative paths of all template files (with subdir prefix)."""
        if not self._dir.is_dir():
            return []
        result: list[str] = []
        for p in sorted(self._dir.rglob("*")):
            if (
                p.is_file()
                and not p.name.startswith(".")
                and p.name != self._GUIDE_FILENAME
                and not self._is_excluded(p)
            ):
                result.append(str(p.relative_to(self._dir)).replace("\\", "/"))
        return result

    def scaffold_to(self, target_dir: Path, *, force: bool = False) -> int:
        """Copy data templates into the target directory, preserving subdirectories.

        Skips existing files unless force=True.
        Excludes engine-only assets (``excel/``) and ``project.yaml``
        (which is placed at the project root, not inside ``data/``).
        Returns the number of files written.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for template in sorted(self._dir.rglob("*")):
            if (
                not template.is_file()
                or template.name.startswith(".")
                or template.name == self._GUIDE_FILENAME
            ):
                continue
            if self._is_excluded(template):
                continue
            rel = template.relative_to(self._dir)
            dest = target_dir / rel
            if dest.exists() and not force:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template, dest)
            count += 1
        return count

    def scaffold_phase_to(
        self, target_dir: Path, phase_id: str, *, force: bool = False,
    ) -> list[str]:
        """Copy the template phase's file set into *target_dir* as phase *phase_id*.

        Every template named ``P1-*`` under any data subdirectory becomes
        ``<phase_id>-*`` with ``P1`` and ``Phase 1`` in its text reworded for
        the new phase, its sentinels intact, so the minted phase audits red
        until authored. Skips existing files unless force=True.
        Returns the relative paths written.
        """
        number = phase_id[1:]
        written: list[str] = []
        for template in sorted(self._dir.rglob(f"{self._PHASE_TEMPLATE_ID}-*")):
            if not template.is_file() or self._is_excluded(template):
                continue
            rel = template.relative_to(self._dir)
            name = rel.name.replace(self._PHASE_TEMPLATE_ID, phase_id, 1)
            dest = target_dir / rel.parent / name
            if dest.exists() and not force:
                continue
            text = template.read_text(encoding="utf-8")
            text = self._PHASE_TEMPLATE_TOKEN.sub(phase_id, text)
            text = text.replace(self._PHASE_TEMPLATE_NAME, f"Phase {number}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            written.append(str(rel.parent / name).replace("\\", "/"))
        return written

    def read_project_template(self) -> str | None:
        """Return the raw text of project.yaml template, or None."""
        path = self._dir / self._PROJECT_FILENAME
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def read_guide(self) -> dict[str, Any]:
        """Read and parse guide.yaml from the templates directory."""
        path = self._dir / self._GUIDE_FILENAME
        if not path.is_file():
            return {"title": "Getting Started", "intro": "", "stages": []}
        return yaml.safe_load(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]

    def _is_excluded(self, path: Path) -> bool:
        """Return True if *path* should be excluded from scaffolding."""
        rel = path.relative_to(self._dir)
        # project.yaml is placed at the project root, not in data/
        if rel.name == self._PROJECT_FILENAME and len(rel.parts) == 1:
            return True
        # engine-only directories (e.g. excel/) contain .xlsx base templates
        return rel.parts[0] in self._SCAFFOLD_EXCLUDE_DIRS
