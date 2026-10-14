"""Integration test for the PlantUML subprocess renderer.

Runs only where a java runtime and the pinned plantuml.jar are both present
(the runtime image ships both at devops/Dockerfile; dev machines may not),
so the suite stays green without a JRE - the route-level behavior is covered
with a faked renderer in test_architecture_api.py either way.
"""

from __future__ import annotations

import shutil

import pytest

from engine.adapters.outbound.plantuml import plantuml_renderer

requires_plantuml = pytest.mark.skipif(
    shutil.which("java") is None or not plantuml_renderer._DEFAULT_JAR.is_file(),
    reason="requires a java runtime and plantuml.jar (the runtime image ships both)",
)

_SOURCE = """@startuml
Alice -> Bob: render request
Bob --> Alice: svg document
@enduml
"""


@requires_plantuml
class TestPlantUmlRenderer:
    def test_renders_svg_via_the_local_process(self) -> None:
        """The pipe render returns an embeddable SVG document (prolog stripped)."""
        svg = plantuml_renderer.PlantUmlRenderer().render_svg(_SOURCE)
        assert svg.startswith("<svg")
        assert "</svg>" in svg
