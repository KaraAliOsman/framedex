from __future__ import annotations

import ast
from pathlib import Path

ENGINE_SOURCE = Path(__file__).resolve().parents[1] / "src" / "dekopen_engine"
FORBIDDEN_IMPORT_ROOTS = {
    "django",
    "http",
    "os",
    "pathlib",
    "psycopg",
    "requests",
    "socket",
    "sqlalchemy",
    "urllib",
}


def _source_trees() -> list[tuple[Path, ast.AST]]:
    trees: list[tuple[Path, ast.AST]] = []
    for path in sorted(ENGINE_SOURCE.glob("*.py")):
        trees.append((path, ast.parse(path.read_text(encoding="utf-8"))))
    return trees


def test_engine_has_no_forbidden_runtime_dependencies_or_io() -> None:
    for path, tree in _source_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.partition(".")[0] for alias in node.names}
                assert roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS), path
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                root = node.module.partition(".")[0]
                assert root not in FORBIDDEN_IMPORT_ROOTS, path
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "open", path


def test_engine_source_contains_no_float_types_or_literals() -> None:
    for path, tree in _source_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id != "float", path
            if isinstance(node, ast.Constant):
                assert not isinstance(node.value, float), path
