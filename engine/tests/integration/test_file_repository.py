"""Integration tests for FileProjectRepository.

Tests the repository interface with non-existent and empty paths to
verify error handling. Full round-trip tests require fixture data files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.adapters.outbound.persistence.file_project_repository import FileProjectRepository
from engine.domain.exceptions import (
    AppError,
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
)


class TestFileProjectRepository:
    """Basic integration tests for FileProjectRepository."""

    def test_can_instantiate(self) -> None:
        """The repository can be instantiated without arguments."""
        repo = FileProjectRepository()
        assert repo is not None

    def test_exists_returns_false_for_missing_path(self, tmp_path: Path) -> None:
        """exists() returns False when no project.yaml is present."""
        repo = FileProjectRepository()
        assert repo.exists(tmp_path) is False

    def test_exists_returns_true_when_project_yaml_present(self, tmp_path: Path) -> None:
        """exists() returns True when project.yaml is present."""
        (tmp_path / "project.yaml").write_text("name: test\n", encoding="utf-8")
        repo = FileProjectRepository()
        assert repo.exists(tmp_path) is True

    def test_load_raises_on_missing_path(self, tmp_path: Path) -> None:
        """load() raises an error when project files are missing."""
        repo = FileProjectRepository()
        bogus = tmp_path / "nonexistent"
        with pytest.raises(AppError):
            repo.load(bogus)

    def test_discover_returns_empty_for_no_projects(self, tmp_path: Path) -> None:
        """discover() returns an empty list when no project.yaml exists."""
        repo = FileProjectRepository()
        assert repo.discover(tmp_path) == []

    def test_discover_finds_project_yaml(self, tmp_path: Path) -> None:
        """discover() finds directories containing project.yaml."""
        proj_dir = tmp_path / "project_a"
        proj_dir.mkdir()
        (proj_dir / "project.yaml").write_text("name: A\n", encoding="utf-8")
        repo = FileProjectRepository()
        found = repo.discover(tmp_path)
        assert len(found) == 1
        assert found[0] == proj_dir

    def test_discover_returns_empty_for_nonexistent_root(self, tmp_path: Path) -> None:
        """discover() returns an empty list when root doesn't exist."""
        repo = FileProjectRepository()
        assert repo.discover(tmp_path / "nope") == []

    def test_delete_removes_project_directory(self, tmp_path: Path) -> None:
        """delete() removes the whole project directory and its contents."""
        proj_dir = tmp_path / "doomed"
        (proj_dir / "data").mkdir(parents=True)
        (proj_dir / "project.yaml").write_text("name: Doomed\n", encoding="utf-8")
        (proj_dir / "data" / "file.tsv").write_text("A\tB\n", encoding="utf-8")
        repo = FileProjectRepository()

        repo.delete(proj_dir)

        assert not proj_dir.exists()

    def test_delete_raises_for_missing_project(self, tmp_path: Path) -> None:
        """delete() raises ProjectNotFoundError when no project.yaml is present."""
        repo = FileProjectRepository()
        with pytest.raises(ProjectNotFoundError):
            repo.delete(tmp_path / "nonexistent")

    def test_rename_moves_the_directory_with_its_contents(self, tmp_path: Path) -> None:
        """rename() moves the whole project directory to the new path."""
        source = tmp_path / "old-slug"
        (source / "data").mkdir(parents=True)
        (source / "project.yaml").write_text("name: Old\n", encoding="utf-8")
        (source / "data" / "file.tsv").write_text("A\tB\n", encoding="utf-8")
        repo = FileProjectRepository()

        repo.rename(source, tmp_path / "new-slug")

        assert not source.exists()
        assert (tmp_path / "new-slug" / "project.yaml").is_file()
        assert (tmp_path / "new-slug" / "data" / "file.tsv").is_file()

    def test_rename_raises_for_missing_source(self, tmp_path: Path) -> None:
        """rename() raises ProjectNotFoundError when the source is not a project."""
        repo = FileProjectRepository()
        with pytest.raises(ProjectNotFoundError):
            repo.rename(tmp_path / "nonexistent", tmp_path / "anywhere")

    def test_rename_refuses_an_occupied_target(self, tmp_path: Path) -> None:
        """rename() raises ProjectAlreadyExistsError and leaves both paths untouched."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "project.yaml").write_text("name: S\n", encoding="utf-8")
        target = tmp_path / "target"
        target.mkdir()
        (target / "project.yaml").write_text("name: T\n", encoding="utf-8")
        repo = FileProjectRepository()

        with pytest.raises(ProjectAlreadyExistsError):
            repo.rename(source, target)

        assert (source / "project.yaml").is_file()
        assert (target / "project.yaml").read_text(encoding="utf-8") == "name: T\n"

    def test_archive_marker_round_trip(self, tmp_path: Path) -> None:
        """set_archived() toggles is_archived() via the marker file."""
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "project.yaml").write_text("name: P\n", encoding="utf-8")
        repo = FileProjectRepository()

        assert repo.is_archived(proj) is False
        repo.set_archived(proj, archived=True)
        assert repo.is_archived(proj) is True
        repo.set_archived(proj, archived=False)
        assert repo.is_archived(proj) is False

    def test_set_archived_raises_for_missing_project(self, tmp_path: Path) -> None:
        """set_archived() raises ProjectNotFoundError when no project.yaml is present."""
        repo = FileProjectRepository()
        with pytest.raises(ProjectNotFoundError):
            repo.set_archived(tmp_path / "nonexistent", archived=True)

    def test_load_config_reads_only_the_config(self, tmp_path: Path) -> None:
        """load_config() returns the ProjectConfig without loading data files."""
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "project.yaml").write_text("name: Config Only\n", encoding="utf-8")
        repo = FileProjectRepository()

        config = repo.load_config(proj)

        assert config.name == "Config Only"

    def test_load_config_raises_for_missing_project(self, tmp_path: Path) -> None:
        """load_config() raises ProjectNotFoundError when no project.yaml is present."""
        repo = FileProjectRepository()
        with pytest.raises(ProjectNotFoundError):
            repo.load_config(tmp_path / "nonexistent")

    def test_delete_raises_for_non_project_directory(self, tmp_path: Path) -> None:
        """delete() refuses a directory that is not a project (no project.yaml)."""
        plain_dir = tmp_path / "not-a-project"
        plain_dir.mkdir()
        (plain_dir / "something.txt").write_text("keep me\n", encoding="utf-8")
        repo = FileProjectRepository()
        with pytest.raises(ProjectNotFoundError):
            repo.delete(plain_dir)
        assert plain_dir.exists()
