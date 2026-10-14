"""Container — the composition root hands out port-satisfying use cases.

Attests INT-ESTIMATEKIT-002: every use case the Container builds satisfies its
declared inbound port. ``Container._check`` raises ``TypeError`` when an
implementation drifts from its port, so this catches signature drift at wiring
time rather than at call time.

Each entry below pairs a Container factory method with the inbound port type its
return value must be an instance of. Building the Container and calling the
factory runs ``_check`` for real; we then assert the returned object is an
instance of the declared port.
"""

from __future__ import annotations

import pytest
from pytest_intent import intent

from engine.application.ports.inbound.append_project_rows import AppendProjectRowsPort
from engine.application.ports.inbound.archive_project import ArchiveProjectPort
from engine.application.ports.inbound.delete_project import DeleteProjectPort
from engine.application.ports.inbound.delete_project_file import DeleteProjectFilePort
from engine.application.ports.inbound.discover_projects import DiscoverProjectsPort
from engine.application.ports.inbound.download_output_file import DownloadOutputFilePort
from engine.application.ports.inbound.export_project import ExportProjectPort
from engine.application.ports.inbound.generate_all import GenerateAllPort
from engine.application.ports.inbound.generate_excels import GenerateExcelsPort
from engine.application.ports.inbound.generate_roadmap import GenerateRoadmapPort
from engine.application.ports.inbound.generate_slides import GenerateSlidesPort
from engine.application.ports.inbound.get_project_summary import GetProjectSummaryPort
from engine.application.ports.inbound.import_project import ImportProjectPort
from engine.application.ports.inbound.list_output_files import ListOutputFilesPort
from engine.application.ports.inbound.list_project_files import ListProjectFilesPort
from engine.application.ports.inbound.read_project_file import ReadProjectFilePort
from engine.application.ports.inbound.rename_project import RenameProjectPort
from engine.application.ports.inbound.replace_project_row import ReplaceProjectRowPort
from engine.application.ports.inbound.run_audit import RunAuditPort
from engine.application.ports.inbound.scaffold_phase import ScaffoldPhasePort
from engine.application.ports.inbound.scaffold_project import ScaffoldProjectPort
from engine.application.ports.inbound.unarchive_project import UnarchiveProjectPort
from engine.application.ports.inbound.write_project_file import WriteProjectFilePort
from engine.container import Container

# (Container factory method name, declared inbound port type).
_FACTORY_PORTS: tuple[tuple[str, type], ...] = (
    ("scaffold_project", ScaffoldProjectPort),
    ("scaffold_phase", ScaffoldPhasePort),
    ("generate_roadmap", GenerateRoadmapPort),
    ("generate_excels", GenerateExcelsPort),
    ("generate_slides", GenerateSlidesPort),
    ("generate_all", GenerateAllPort),
    ("discover_projects", DiscoverProjectsPort),
    ("delete_project", DeleteProjectPort),
    ("rename_project", RenameProjectPort),
    ("archive_project", ArchiveProjectPort),
    ("unarchive_project", UnarchiveProjectPort),
    ("get_project_summary", GetProjectSummaryPort),
    ("list_project_files", ListProjectFilesPort),
    ("read_project_file", ReadProjectFilePort),
    ("write_project_file", WriteProjectFilePort),
    ("append_project_rows", AppendProjectRowsPort),
    ("replace_project_row", ReplaceProjectRowPort),
    ("delete_project_file", DeleteProjectFilePort),
    ("list_output_files", ListOutputFilesPort),
    ("download_output_file", DownloadOutputFilePort),
    ("export_project", ExportProjectPort),
    ("import_project", ImportProjectPort),
    ("run_audit", RunAuditPort),
)


@intent("INT-ESTIMATEKIT-002")
def test_every_factory_returns_its_declared_inbound_port() -> None:
    """INT-ESTIMATEKIT-002: each use case the Container hands out satisfies its port."""
    container = Container()
    for method_name, port in _FACTORY_PORTS:
        use_case = getattr(container, method_name)()
        assert isinstance(use_case, port), (
            f"Container.{method_name}() returned {type(use_case).__name__}, "
            f"which does not satisfy {port.__name__}"
        )


def test_check_rejects_drifted_implementation() -> None:
    """Container._check fails closed: a non-conforming object raises TypeError."""
    from engine.container import _check

    class NotAPort:
        pass

    with pytest.raises(TypeError):
        _check(NotAPort(), RunAuditPort)
