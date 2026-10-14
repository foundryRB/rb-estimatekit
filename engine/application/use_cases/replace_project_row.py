"""Use case: Replace one row of a project's TSV data file by its ID."""

from __future__ import annotations

from pathlib import Path

from engine.application.events import FILE_WRITTEN, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.exceptions import InvalidRowError
from engine.domain.services.tsv_text import (
    cells_for_row,
    id_column,
    replace_row,
    row_numbers,
    row_write_header,
)
from engine.logging import get_logger

logger = get_logger(__name__)


class ReplaceProjectRow:
    """Replace the one row of a TSV data file whose ID column holds a given ID.

    The ID column is the header's first column named ``... ID`` (``Req ID``,
    ``Activity ID``, ``Assumption ID``, ``Guideline ID``, ``Phase ID``). The new
    row is checked against the header, keeps its ID, and must match exactly one
    existing row; every other row stays byte for byte as it was, line endings
    included.
    """

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def execute(
        self, project_path: Path, relative_path: str, row_id: str, row: dict[str, str]
    ) -> None:
        """Replace the row of *relative_path* whose ID is *row_id* with *row*."""
        text = self._repository.read_data_file_exact(project_path, relative_path)
        header = row_write_header(relative_path, text)
        key = id_column(header)
        if key is None:
            raise InvalidRowError(
                relative_path, "the file has no ID column; rewrite the whole file"
            )
        wanted = row_id.strip()
        if not wanted:
            raise InvalidRowError(relative_path, f"a blank {key} names no row")
        try:
            cells = cells_for_row(header, row)
        except ValueError as exc:
            raise InvalidRowError(relative_path, str(exc)) from exc
        if cells[header.index(key)].strip() != wanted:
            raise InvalidRowError(relative_path, f"the row's {key} must stay {wanted!r}")
        matches = row_numbers(text, key, wanted)
        if len(matches) != 1:
            found = "no row" if not matches else f"{len(matches)} rows"
            raise InvalidRowError(
                relative_path, f"{found} with {key} {wanted!r}; exactly one must match"
            )
        text = replace_row(text, matches[0], cells)
        self._repository.write_data_file_exact(project_path, relative_path, text)
        logger.info("Replaced %s %s in %s of %s", key, wanted, relative_path, project_path.name)
        state_fact(
            self._events,
            event_type=FILE_WRITTEN,
            subject=project_path.name,
            data={"project": project_path.name, "path": relative_path},
        )
