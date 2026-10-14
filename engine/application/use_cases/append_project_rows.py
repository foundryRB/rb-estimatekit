"""Use case: Append rows to a project's TSV data file."""

from __future__ import annotations

from pathlib import Path

from engine.application.events import FILE_WRITTEN, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.exceptions import InvalidRowError
from engine.domain.services.tsv_text import (
    append_row,
    cells_for_row,
    column_values,
    id_column,
    row_write_header,
)
from engine.logging import get_logger

logger = get_logger(__name__)


class AppendProjectRows:
    """Append rows to a TSV data file without re-sending the rows it already holds.

    Every row is checked against the file's header row, the parsing contract,
    before anything is written, so a refused call leaves the file untouched. In
    a file with an ID column, each appended row carries a non-blank ID new to
    the file. The rows already in the file stay byte for byte as they were, line
    endings included.
    """

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def execute(
        self, project_path: Path, relative_path: str, rows: list[dict[str, str]]
    ) -> int:
        """Append *rows* to the file at *relative_path*; return how many were appended."""
        text = self._repository.read_data_file_exact(project_path, relative_path)
        header = row_write_header(relative_path, text)
        if not rows:
            raise InvalidRowError(relative_path, "no rows to append")
        key = id_column(header)
        in_file = {value for value in column_values(text, key) if value} if key else set()
        given: set[str] = set()
        all_cells = []
        for number, row in enumerate(rows, start=1):
            try:
                cells = cells_for_row(header, row)
            except ValueError as exc:
                raise InvalidRowError(relative_path, f"row {number}: {exc}") from exc
            if key is not None:
                row_id = cells[header.index(key)].strip()
                if not row_id:
                    raise InvalidRowError(relative_path, f"row {number}: a blank {key}")
                if row_id in in_file:
                    raise InvalidRowError(
                        relative_path, f"row {number}: {key} {row_id!r} is already in the file"
                    )
                if row_id in given:
                    raise InvalidRowError(
                        relative_path, f"row {number}: {key} {row_id!r} repeats an earlier row"
                    )
                given.add(row_id)
            all_cells.append(cells)
        for cells in all_cells:
            text = append_row(text, cells)
        self._repository.write_data_file_exact(project_path, relative_path, text)
        logger.info("Appended %d row(s) to %s in %s", len(rows), relative_path, project_path.name)
        state_fact(
            self._events,
            event_type=FILE_WRITTEN,
            subject=project_path.name,
            data={"project": project_path.name, "path": relative_path},
        )
        return len(rows)
