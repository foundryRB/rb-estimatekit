"""DomainPurity — the hexagonal centre imports nothing from the outer rings.

Attests INT-ESTIMATEKIT-001: every module under ``engine.domain`` imports only
the Python standard library and other ``engine.domain`` modules — never
``engine.application``, ``engine.adapters``, or a third-party framework.

The check is a static AST scan of the domain package source. It walks every
``.py`` file under the domain package, parses its ``import`` / ``from ... import``
statements, and asserts none of them reaches into an outer ring or a known
third-party framework. A static scan (rather than runtime ``sys.modules``
inspection) catches the violation even on a module that the test run never
happens to import.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

from pytest_intent import intent

import engine.domain as domain_pkg

# Top-level package names that must never appear in a domain import.
_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    # Inner ring must not depend on outer rings.
    "engine.application",
    "engine.adapters",
    "engine.container",
    # Known third-party frameworks / libraries the domain must stay free of.
    "fastapi",
    "starlette",
    "uvicorn",
    "pydantic",
    "openpyxl",
    "yaml",
    "httpx",
    "click",
)


def _domain_module_names() -> list[str]:
    """Every importable module name under the ``engine.domain`` package."""
    names = [domain_pkg.__name__]
    for mod in pkgutil.walk_packages(domain_pkg.__path__, prefix=domain_pkg.__name__ + "."):
        names.append(mod.name)
    return names


def _imported_targets(source: str) -> set[str]:
    """Fully-qualified module targets referenced by import statements in *source*."""
    targets: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        # Skip relative imports (level > 0): they resolve within engine.domain.
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            targets.add(node.module)
    return targets


def test_domain_package_has_modules() -> None:
    """Sanity: the walk actually finds the domain modules it is meant to police."""
    names = _domain_module_names()
    assert len(names) > 5
    assert any(n.endswith("value_objects.project_slug") for n in names)


@intent("INT-ESTIMATEKIT-001")
def test_domain_imports_only_stdlib_and_domain() -> None:
    """INT-ESTIMATEKIT-001: no engine.domain module imports an outer ring or framework."""
    violations: list[str] = []
    for name in _domain_module_names():
        module = importlib.import_module(name)
        source_file = getattr(module, "__file__", None)
        if not source_file:
            continue
        source = Path(source_file).read_text(encoding="utf-8")
        for target in _imported_targets(source):
            for forbidden in _FORBIDDEN_PREFIXES:
                if target == forbidden or target.startswith(forbidden + "."):
                    violations.append(f"{name} imports {target}")
    assert not violations, "domain purity violated:\n" + "\n".join(sorted(violations))
