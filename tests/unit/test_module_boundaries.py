"""Enforce the ADR-0001 module boundaries by inspecting imports."""

import ast
from pathlib import Path

import pytest

PACKAGE_DIR = Path(__file__).parents[2] / "src" / "runguard"

# Internal packages each analysis module may import, including itself.
ALLOWED_INTERNAL = {
    "domain": {"domain"},
    "comparison": {"domain", "comparison"},
    "statistics": {"domain", "comparison", "statistics"},
}
# Packages the runtime must never import (tracking SDKs, test-only references).
FORBIDDEN_EXTERNAL = {"wandb", "mlflow", "numpy", "scipy"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


@pytest.mark.parametrize("module", sorted(ALLOWED_INTERNAL))
def test_analysis_modules_respect_internal_boundaries(module: str) -> None:
    violations = []
    for path in sorted((PACKAGE_DIR / module).rglob("*.py")):
        for name in _imports(path):
            parts = name.split(".")
            if parts[0] == "runguard" and len(parts) > 1:
                if parts[1] not in ALLOWED_INTERNAL[module]:
                    violations.append(f"{path.name}: {name}")

    assert violations == []


def test_runtime_does_not_import_forbidden_packages() -> None:
    violations = [
        f"{path.relative_to(PACKAGE_DIR)}: {name}"
        for path in sorted(PACKAGE_DIR.rglob("*.py"))
        for name in _imports(path)
        if name.split(".")[0] in FORBIDDEN_EXTERNAL
    ]

    assert violations == []
