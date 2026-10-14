"""Use case: Scaffold a new project from templates."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from engine.application.events import PROJECT_SCAFFOLDED, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.template_repository import TemplateRepository
from engine.domain.constants.files.inputs import DATA_SUBDIRS
from engine.domain.exceptions import ConfigurationError, ProjectAlreadyExistsError
from engine.logging import get_logger

logger = get_logger(__name__)


class ScaffoldProject:
    """Create a new project directory with all template files."""

    def __init__(
        self, templates: TemplateRepository, events: EventPublisher | None = None
    ) -> None:
        self._templates = templates
        self._events = events

    def execute(self, projects_root: Path, slug: str, *, force: bool = False) -> Path:
        """Scaffold a new project.

        Creates the project directory, data/ and output/ subdirectories,
        copies all templates into data/, and creates a minimal project.yaml.

        Raises ProjectAlreadyExistsError if the project already exists
        and ``force`` is False.

        Returns the path to the created project.
        """
        target = projects_root / slug

        if (target / "project.yaml").exists() and not force:
            raise ProjectAlreadyExistsError(target)

        target.mkdir(parents=True, exist_ok=True)
        data_dir = target / "data"
        data_dir.mkdir(exist_ok=True)
        for subdir in DATA_SUBDIRS:
            (data_dir / subdir).mkdir(exist_ok=True)
        (target / "output").mkdir(exist_ok=True)

        self._templates.scaffold_to(data_dir, force=force)

        # Create project.yaml — use template file if available, else generate
        config_path = target / "project.yaml"
        if not config_path.exists() or force:
            template_text = self._templates.read_project_template()
            if template_text is not None:
                # Personalise the template with slug-derived defaults
                pretty_name = slug.replace("-", " ").title()
                now = datetime.now()
                text = template_text.replace(
                    "[EXAMPLE] Project Name", pretty_name,
                ).replace(
                    "[EXAMPLE] short-name", slug,
                ).replace(
                    "[EXAMPLE] Platform description",
                    f"[EXAMPLE] {pretty_name} platform",
                )
                # Update the date line to current month
                text = re.sub(
                    r'^(date:\s*").*(")$',
                    rf'\g<1>{now.strftime("%B %Y")}\2',
                    text,
                    flags=re.MULTILINE,
                )
                config_path.write_text(text, encoding="utf-8")
            else:
                raise ConfigurationError(
                    "templates/project.yaml", "not found — cannot scaffold project"
                )

        logger.info("Scaffolded project %s at %s", slug, target)
        # The project is on disk before the fact is stated; the event carries the
        # slug and nothing of the scaffold's content (REF-Events section 5).
        state_fact(
            self._events, event_type=PROJECT_SCAFFOLDED, subject=slug, data={"project": slug}
        )
        return target
